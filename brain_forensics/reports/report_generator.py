import os
import sys
import json
import time
import traceback
from datetime import datetime, timezone
from fpdf import FPDF
from glob import glob

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import config
except ImportError:
    print("Error: Could not import config from report_generator.py", file=sys.stderr)
    # Define fallback config paths if necessary
    class MockConfig:
        REPORTS_DIR = "reports"
        CASES_DIR = "cases"
        CASE_DATA_DIR_NAME = "data"
        CASE_METADATA_DIR_NAME = "metadata"
        CASE_ANALYSIS_DIR_NAME = "analysis"
        TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
        HASH_ALGORITHM = "sha256"
        REPORT_AUTHOR = "Forensic Analyst"
    config = MockConfig()

class PDFReport(FPDF):
    """Custom FPDF class with header and footer."""    
    def __init__(self, case_name, target_user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_name = case_name
        self.target_user = target_user
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, 15)
        self.alias_nb_pages()
        self.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True) # Use a font supporting more characters
        self.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
        self.add_font('DejaVu', 'I', 'DejaVuSans-Oblique.ttf', uni=True)
        self.add_font('DejaVuMono', '', 'DejaVuSansMono.ttf', uni=True)
        self.set_font('DejaVu', '', 10)

    def header(self):
        self.set_font('DejaVu', 'B', 12)
        self.cell(0, 10, f'{config.APP_NAME} - Forensic Report', 0, 1, 'C')
        self.set_font('DejaVu', '', 8)
        self.cell(0, 5, f'Case: {self.case_name} | Target: {self.target_user}', 0, 1, 'C')
        self.ln(5) # Add space after header

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')
        timestamp = datetime.now(timezone.utc).strftime(config.TIMESTAMP_FORMAT)
        self.set_xy(-50, -15)
        self.cell(0, 10, f'Generated: {timestamp}', 0, 0, 'R')

    def chapter_title(self, title):
        self.set_font('DejaVu', 'B', 14)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 8, title, 0, 1, 'L', fill=True)
        self.ln(4)
        self.set_font('DejaVu', '', 10)

    def chapter_body(self, body):
        self.set_font('DejaVu', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()

    def code_block(self, text):
        self.set_font('DejaVuMono', '', 9)
        self.set_fill_color(245, 245, 245)
        self.multi_cell(0, 5, text, border=1, fill=True)
        self.ln(2)
        self.set_font('DejaVu', '', 10)

    def add_image(self, image_path, title=""):
        if image_path and os.path.exists(image_path):
            if title:
                 self.set_font('DejaVu', 'B', 11)
                 self.cell(0, 8, title, 0, 1, 'L')
                 self.ln(1)
            try:
                # Calculate image size to fit page width
                page_width = self.w - self.l_margin - self.r_margin
                self.image(image_path, w=page_width * 0.8, x=self.l_margin + page_width * 0.1)
                self.ln(5)
            except Exception as e:
                self.set_text_color(255, 0, 0) # Red
                self.chapter_body(f"Error embedding image {os.path.basename(image_path)}: {e}")
                self.set_text_color(0, 0, 0)
        else:
             self.set_font('DejaVu', 'I', 9)
             self.cell(0, 5, f"[Image not available: {os.path.basename(image_path or '')}]")
             self.ln(5)

    def evidence_table(self, headers, data):
        if not data:
             self.chapter_body("No evidence items to display.")
             return
        
        self.set_font('DejaVu', 'B', 9)
        col_widths = [self.get_string_width(h) + 6 for h in headers] # Initial widths based on headers
        # Adjust widths based on data
        self.set_font('DejaVu', '', 8)
        for row in data:
            for i, item in enumerate(row):
                col_widths[i] = max(col_widths[i], self.get_string_width(str(item)) + 6)
        
        total_width = sum(col_widths)
        page_width = self.w - self.l_margin - self.r_margin
        # Scale widths if they exceed page width
        if total_width > page_width:
            scale_factor = page_width / total_width
            col_widths = [w * scale_factor for w in col_widths]

        # Draw Header
        self.set_font('DejaVu', 'B', 9)
        self.set_fill_color(220, 220, 220)
        self.set_line_width(0.3)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, border=1, fill=True, align='C')
        self.ln()

        # Draw Data Rows
        self.set_font('DejaVu', '', 8)
        self.set_fill_color(255, 255, 255)
        fill = False
        for row in data:
            for i, item in enumerate(row):
                self.cell(col_widths[i], 6, str(item), border='LR', fill=fill)
            self.ln()
            fill = not fill
        # Closing line
        self.cell(sum(col_widths), 0, '', 'T')
        self.ln()
        self.set_font('DejaVu', '', 10)

class ForensicReportGenerator:
    """
    Generates a detailed PDF forensic report from case data.
    """
    def __init__(self):
        self.output_dir = config.REPORTS_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_case_paths(self, case_name):
        """Get all relevant paths for a case."""
        safe_case_name = os.path.basename(case_name)
        if not safe_case_name or safe_case_name == '.' or safe_case_name == '..':
            return None
        case_path = os.path.join(config.CASES_DIR, safe_case_name)
        if not os.path.isdir(case_path):
            return None
        paths = {
            "case": case_path,
            "data": os.path.join(case_path, config.CASE_DATA_DIR_NAME),
            "metadata": os.path.join(case_path, config.CASE_METADATA_DIR_NAME),
            "analysis": os.path.join(case_path, config.CASE_ANALYSIS_DIR_NAME),
            "log": os.path.join(case_path, config.CASE_METADATA_DIR_NAME, "forensic_log.jsonl")
        }
        return paths

    def _read_json_file(self, filepath, default=None):
        """Safely read a JSON file."""
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading JSON file {filepath}: {e}", file=sys.stderr)
        return default

    def _format_analysis_summary(self, sentiment_results, network_vis_path):
        """Format the analysis summary text."""
        summary = "Analysis Results:\n\n"
        if sentiment_results:
            summary += f"- Sentiment Analysis:\n"
            summary += f"  - Average Sentiment Score: {sentiment_results.get('average_sentiment', 'N/A'):.3f}\n"
            dist = sentiment_results.get('sentiment_distribution', {})
            summary += f"  - Distribution: Positive={dist.get('positive', 0)}, Neutral={dist.get('neutral', 0)}, Negative={dist.get('negative', 0)}\n"
            keywords = ", ".join(sentiment_results.get('top_keywords', []))
            summary += f"  - Top Keywords: {keywords}\n"
        else:
            summary += "- Sentiment Analysis: Not available or failed.\n"
        
        summary += "\n- Network Analysis:\n"
        if network_vis_path and os.path.exists(network_vis_path):
            summary += f"  - Visualization generated: {os.path.basename(network_vis_path)}\n"
        else:
            summary += "  - Visualization not available or failed.\n"
            
        # Placeholder for future analyses
        summary += "\n- Image Analysis: Not implemented in this version.\n"
        summary += "- Timeline Analysis: Not implemented in this version.\n"
        return summary

    def _get_evidence_items(self, paths):
        """Collect evidence items details from metadata files."""
        items = []
        metadata_files = glob(os.path.join(paths['metadata'], "*_meta.json"))
        for meta_file in metadata_files:
            metadata = self._read_json_file(meta_file)
            if metadata:
                 items.append([
                     metadata.get("data_filename", "N/A"),
                     metadata.get("source_platform", "N/A"),
                     metadata.get("collection_timestamp_utc", "N/A"),
                     metadata.get("hash_algorithm", "N/A"),
                     metadata.get("data_hash", "N/A")[:16] + "..." # Shorten hash for table
                 ])
        return items

    def generate_report(self, case_name, case_path, target_info, sentiment_results=None, network_vis_path=None):
        """
        Generate a PDF forensic report for the specified case.

        Args:
            case_name (str): The name of the case.
            case_path (str): Absolute path to the case directory.
            target_info (dict): Information about the target and collection parameters.
            sentiment_results (dict, optional): Results from sentiment analysis.
            network_vis_path (str, optional): Path to the network visualization image.

        Returns:
            str: Absolute path to the generated PDF report, or None on failure.
        """
        paths = self._get_case_paths(case_name)
        if not paths:
             print(f"Error: Could not find valid paths for case '{case_name}'", file=sys.stderr)
             return None
        
        report_filename = f"ForensicReport_{case_name}_{int(time.time())}.pdf"
        output_path = os.path.join(self.output_dir, report_filename)
        
        pdf = PDFReport(case_name, target_info.get('target', 'N/A'))
        pdf.set_title(f"Forensic Report - Case: {case_name}")
        pdf.set_author(config.REPORT_AUTHOR)
        pdf.add_page()
        
        try:
            # --- 1. Case Overview --- 
            pdf.chapter_title("1. Case Overview")
            overview_body = (
                f"Case Name: {case_name}\n"
                f"Date Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                f"Generated By: {config.REPORT_AUTHOR}\n\n"
                f"Target Identifier: {target_info.get('target', 'N/A')}\n"
                f"Platforms Investigated: {', '.join(target_info.get('platforms', []))}\n"
                # Add more details from target_info['parameters'] if available
            )
            pdf.chapter_body(overview_body)

            # --- 2. Methodology --- 
            pdf.chapter_title("2. Methodology")
            methodology = (
                f"This report details the findings from the analysis of social media data related to the target identifier using the {config.APP_NAME} v{config.VERSION}. "
                f"Data was collected using simulated web search queries targeting the specified platforms. "
                f"Collected items were preserved by saving the structured data and associated metadata. "
                f"Data integrity was verified using the {config.HASH_ALGORITHM} hashing algorithm. "
                f"Analysis performed includes sentiment analysis using the '{config.LLM_MODEL}' model and simulated network connection visualization. "
                f"All actions were logged in the case forensic log file."
            )
            pdf.chapter_body(methodology)

            # --- 3. Evidence Collected --- 
            pdf.chapter_title("3. Evidence Summary")
            evidence_items = self._get_evidence_items(paths)
            if evidence_items:
                pdf.chapter_body(f"A total of {len(evidence_items)} items were collected and preserved.")
                headers = ["Filename", "Platform", "Collected (UTC)", "Hash Alg", "Data Hash (SHA256)"]
                pdf.evidence_table(headers, evidence_items)
            else:
                pdf.chapter_body("No evidence items were found or preserved for this case.")

            # --- 4. Analysis Findings --- 
            pdf.chapter_title("4. Analysis Findings")
            analysis_summary = self._format_analysis_summary(sentiment_results, network_vis_path)
            pdf.chapter_body(analysis_summary)
            
            # Embed Network Graph if available
            if network_vis_path and os.path.exists(network_vis_path):
                 pdf.add_image(network_vis_path, title="Network Visualization")
            
            # TODO: Embed sentiment charts, timeline visualizations when implemented

            # --- 5. Forensic Log --- 
            pdf.add_page() # New page for log
            pdf.chapter_title("5. Forensic Log Summary")
            if os.path.exists(paths['log']):
                log_lines = []
                try:
                    with open(paths['log'], 'r', encoding='utf-8') as log_f:
                         for line in log_f:
                             try:
                                 entry = json.loads(line)
                                 # Format for readability
                                 ts = entry.get("log_timestamp_utc", "")
                                 evt = entry.get("event_type", "")
                                 msg = f"[{ts}] {evt}: " + ", ".join(f"{k}={v}" for k,v in entry.items() if k not in ["log_timestamp_utc", "event_type"])
                                 log_lines.append(msg)
                             except json.JSONDecodeError:
                                 log_lines.append(f"[RAW] {line.strip()}") # Show raw if parse fails
                except Exception as log_e:
                    pdf.chapter_body(f"Error reading forensic log: {log_e}")
                
                if log_lines:
                    pdf.code_block("\n".join(log_lines[-50:])) # Show last 50 lines max
                    if len(log_lines) > 50:
                        pdf.chapter_body("(Log truncated for brevity. Full log available in case files.)")
                else:
                     pdf.chapter_body("Forensic log file is empty.")
            else:
                pdf.chapter_body("Forensic log file not found.")

            # --- 6. Conclusion --- 
            pdf.chapter_title("6. Conclusion")
            pdf.chapter_body(
                "This report summarizes the collection, preservation, and analysis conducted for this case. "
                "Refer to the evidence summary and forensic log for detailed information. "
                "Further investigation may be required based on these findings."
                ) 

            # --- Save PDF --- 
            pdf.output(output_path, 'F')
            print(f"Forensic report successfully generated: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Fatal error during PDF report generation: {e}", file=sys.stderr)
            traceback.print_exc()
            return None

# Example Usage (if run directly)
if __name__ == "__main__":
    if len(sys.argv) > 1:
        case_name_to_report = sys.argv[1]
        print(f"Generating report for case: {case_name_to_report}")
        
        # Need dummy data/paths for standalone execution
        paths = {
             "case": os.path.join(config.CASES_DIR, case_name_to_report),
             "analysis": os.path.join(config.CASES_DIR, case_name_to_report, config.CASE_ANALYSIS_DIR_NAME),
             "metadata": os.path.join(config.CASES_DIR, case_name_to_report, config.CASE_METADATA_DIR_NAME)
        }
        dummy_target_info = {'target': 'dummy_target', 'platforms': ['X']}
        # Try to load actual analysis results if they exist
        dummy_sentiment = ForensicReportGenerator()._read_json_file(os.path.join(paths['analysis'], 'sentiment_results.json'), default={})
        # Find a network graph image if it exists
        network_graphs = glob(os.path.join(paths['analysis'], 'network_graph*.png'))
        dummy_network_path = network_graphs[0] if network_graphs else None

        generator = ForensicReportGenerator()
        report_file = generator.generate_report(
            case_name_to_report, 
            paths['case'], 
            dummy_target_info, 
            dummy_sentiment, 
            dummy_network_path
        )
        if report_file:
            print(f"\nReport saved to: {report_file}")
        else:
            print(f"Report generation failed for case '{case_name_to_report}'.")
    else:
        print("Usage: python report_generator.py <case_name>")
        print("Ensure the case exists in the 'cases' directory and has analysis results.") 