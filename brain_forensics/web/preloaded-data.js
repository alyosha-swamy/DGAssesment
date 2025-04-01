/**
 * Preloaded data for Social Media Analysis Visualization Tool
 * This file contains sample datasets for network analysis, sentiment analysis, and timeline tracking
 */

const PRELOADED_DATA = {
    // User Profile 1 - Tech Influencer
    user1: {
        meta: {
            id: "user1",
            name: "Tech Influencer",
            description: "Technology influencer with significant reach and engagement",
            dataPoints: 1872
        },
        network: {
            // Base64 encoded network graph image
            image: null, // We'll use canvas rendering instead
            nodes: [
                { id: "central", label: "@techinfluencer", type: "account", size: 25, importance: 95 },
                { id: "n1", label: "@techblog", type: "account", size: 18, importance: 85 },
                { id: "n2", label: "@newsgadget", type: "account", size: 15, importance: 70 },
                { id: "n3", label: "@reviewchannel", type: "account", size: 14, importance: 68 },
                { id: "n4", label: "@competitor", type: "account", size: 12, importance: 60 },
                { id: "n5", label: "#techtips", type: "hashtag", size: 16, importance: 78 },
                { id: "n6", label: "#newgadgets", type: "hashtag", size: 14, importance: 75 },
                { id: "n7", label: "#productlaunch", type: "hashtag", size: 12, importance: 62 },
                { id: "n8", label: "@techfan1", type: "account", size: 10, importance: 50 },
                { id: "n9", label: "@techfan2", type: "account", size: 10, importance: 48 }
            ],
            edges: [
                { source: "central", target: "n1", weight: 9, type: "mention" },
                { source: "central", target: "n2", weight: 7, type: "mention" },
                { source: "central", target: "n3", weight: 6, type: "mention" },
                { source: "central", target: "n5", weight: 8, type: "used_hashtag" },
                { source: "central", target: "n6", weight: 7, type: "used_hashtag" },
                { source: "central", target: "n7", weight: 5, type: "used_hashtag" },
                { source: "n1", target: "central", weight: 8, type: "mention" },
                { source: "n2", target: "central", weight: 5, type: "mention" },
                { source: "n3", target: "central", weight: 4, type: "mention" },
                { source: "n4", target: "central", weight: 3, type: "mention" },
                { source: "n4", target: "n1", weight: 2, type: "mention" },
                { source: "n5", target: "n6", weight: 6, type: "cooccurrence" },
                { source: "n8", target: "central", weight: 2, type: "mention" },
                { source: "n9", target: "central", weight: 2, type: "mention" }
            ],
            clusters: [
                { id: "c1", name: "Core Tech Community", nodes: ["central", "n1", "n2", "n3"] },
                { id: "c2", name: "Trending Hashtags", nodes: ["n5", "n6", "n7"] },
                { id: "c3", name: "Audience", nodes: ["n8", "n9"] }
            ],
            keyNodes: [
                {
                    id: "central",
                    title: "@techinfluencer",
                    description: "Central figure in the network with highest connection count",
                    score: 95
                },
                {
                    id: "n1",
                    title: "@techblog → @techinfluencer",
                    description: "Strong bidirectional relationship with 17 interactions in the past month",
                    score: 85
                },
                {
                    id: "n5",
                    title: "#techtips",
                    description: "Most used hashtag appearing in 78% of content",
                    score: 78
                }
            ]
        },
        sentiment: {
            average: 0.65,
            distribution: {
                "Positive": 65,
                "Neutral": 25,
                "Negative": 10
            },
            trend: [0.5, 0.6, 0.7, 0.55, 0.6, 0.75, 0.8, 0.7, 0.6, 0.65],
            keywords: [
                { word: "innovation", score: 0.82, count: 47 },
                { word: "launch", score: 0.75, count: 36 },
                { word: "review", score: 0.62, count: 28 },
                { word: "improvement", score: 0.71, count: 25 },
                { word: "excited", score: 0.88, count: 22 }
            ]
        },
        timeline: {
            dates: ["2023-01", "2023-02", "2023-03", "2023-04", "2023-05", 
                    "2023-06", "2023-07", "2023-08", "2023-09", "2023-10"],
            metrics: {
                posts: [34, 32, 45, 38, 52, 58, 63, 55, 61, 72],
                engagement: [1200, 1340, 2500, 1980, 3100, 3800, 4200, 3600, 3900, 4800],
                reach: [15000, 16200, 22000, 19500, 28000, 34000, 38000, 32000, 36000, 42000]
            },
            events: [
                {
                    date: "2023-03-15",
                    title: "Product Launch Coverage",
                    description: "Coverage of major tech product launch resulted in 3X normal engagement"
                },
                {
                    date: "2023-06-22",
                    title: "Viral Post",
                    description: "Post about emerging AI technology went viral with 6X normal engagement"
                },
                {
                    date: "2023-10-05",
                    title: "Tech Conference",
                    description: "Live updates from industry conference led to follower growth spike"
                }
            ]
        }
    },
    
    // User Profile 2 - Suspicious Activity
    user2: {
        meta: {
            id: "user2",
            name: "Suspicious Account",
            description: "Account exhibiting unusual activity patterns suggestive of inauthentic behavior",
            dataPoints: 1284
        },
        network: {
            image: null,
            nodes: [
                { id: "central", label: "@suspicious_user", type: "account", size: 20, importance: 80 },
                { id: "n1", label: "@similar_account1", type: "account", size: 18, importance: 75 },
                { id: "n2", label: "@similar_account2", type: "account", size: 18, importance: 75 },
                { id: "n3", label: "@similar_account3", type: "account", size: 18, importance: 75 },
                { id: "n4", label: "@controller", type: "account", size: 22, importance: 90 },
                { id: "n5", label: "#political_topic1", type: "hashtag", size: 15, importance: 65 },
                { id: "n6", label: "#political_topic2", type: "hashtag", size: 15, importance: 65 },
                { id: "n7", label: "@target_account1", type: "account", size: 14, importance: 60 },
                { id: "n8", label: "@target_account2", type: "account", size: 14, importance: 60 },
                { id: "n9", label: "@legitimate_user", type: "account", size: 10, importance: 40 },
                { id: "n10", label: "@legitimate_user2", type: "account", size: 10, importance: 40 }
            ],
            edges: [
                { source: "central", target: "n1", weight: 9, type: "coordinated" },
                { source: "central", target: "n2", weight: 9, type: "coordinated" },
                { source: "central", target: "n3", weight: 9, type: "coordinated" },
                { source: "central", target: "n4", weight: 10, type: "coordinated" },
                { source: "central", target: "n5", weight: 8, type: "used_hashtag" },
                { source: "central", target: "n6", weight: 8, type: "used_hashtag" },
                { source: "central", target: "n7", weight: 7, type: "mention" },
                { source: "central", target: "n8", weight: 7, type: "mention" },
                { source: "n1", target: "n5", weight: 8, type: "used_hashtag" },
                { source: "n2", target: "n5", weight: 8, type: "used_hashtag" },
                { source: "n3", target: "n5", weight: 8, type: "used_hashtag" },
                { source: "n1", target: "n7", weight: 7, type: "mention" },
                { source: "n2", target: "n7", weight: 7, type: "mention" },
                { source: "n3", target: "n8", weight: 7, type: "mention" },
                { source: "n4", target: "n1", weight: 6, type: "coordinated" },
                { source: "n4", target: "n2", weight: 6, type: "coordinated" },
                { source: "n4", target: "n3", weight: 6, type: "coordinated" },
                { source: "n9", target: "n7", weight: 2, type: "mention" },
                { source: "n10", target: "n8", weight: 2, type: "mention" }
            ],
            clusters: [
                { id: "c1", name: "Coordinated Accounts", nodes: ["central", "n1", "n2", "n3", "n4"] },
                { id: "c2", name: "Target Accounts", nodes: ["n7", "n8"] },
                { id: "c3", name: "Regular Users", nodes: ["n9", "n10"] }
            ],
            keyNodes: [
                {
                    id: "n4",
                    title: "Potential Controller Account",
                    description: "Hub account with high coordination patterns among similar accounts",
                    score: 90,
                    suspicious: true
                },
                {
                    id: "c1",
                    title: "COORDINATED ACTIVITY",
                    description: "Group of 5 accounts posting nearly identical content within 3-minute windows",
                    score: 95,
                    suspicious: true
                },
                {
                    id: "n5",
                    title: "Targeted Hashtag",
                    description: "Hashtag being amplified by coordinated accounts, timing suggests deliberate campaign",
                    score: 85,
                    suspicious: true
                }
            ]
        },
        sentiment: {
            average: -0.72,
            distribution: {
                "Positive": 8,
                "Neutral": 20,
                "Negative": 72
            },
            trend: [-0.6, -0.7, -0.65, -0.8, -0.75, -0.7, -0.8, -0.9, -0.7, -0.6],
            keywords: [
                { word: "attack", score: -0.85, count: 58 },
                { word: "corrupt", score: -0.9, count: 45 },
                { word: "scandal", score: -0.8, count: 42 },
                { word: "failure", score: -0.75, count: 36 },
                { word: "outrage", score: -0.82, count: 33 }
            ]
        },
        timeline: {
            dates: ["2023-01", "2023-02", "2023-03", "2023-04", "2023-05", 
                    "2023-06", "2023-07", "2023-08", "2023-09", "2023-10"],
            metrics: {
                posts: [15, 18, 22, 142, 168, 175, 150, 160, 155, 25],
                engagement: [320, 380, 420, 1850, 2100, 2300, 1950, 2050, 1900, 400],
                reach: [4800, 5200, 5600, 22000, 28000, 26000, 24000, 25000, 23000, 6000]
            },
            events: [
                {
                    date: "2023-04-02",
                    title: "ACTIVITY SPIKE BEGINS",
                    description: "Sudden 600% increase in posting activity with synchronized timing",
                    suspicious: true
                },
                {
                    date: "2023-04-15",
                    title: "NARRATIVE SHIFT",
                    description: "Coordinated introduction of specific messaging across multiple accounts",
                    suspicious: true
                },
                {
                    date: "2023-09-28",
                    title: "ACTIVITY DECLINE",
                    description: "Abrupt drop in activity across all associated accounts",
                    suspicious: true
                }
            ]
        }
    },
    
    // Hashtag Analysis
    hashtag1: {
        meta: {
            id: "hashtag1",
            name: "#trending Hashtag Analysis",
            description: "Analysis of engagement and usage patterns for a trending hashtag",
            dataPoints: 2450
        },
        network: {
            image: null,
            nodes: [
                { id: "central", label: "#trending", type: "hashtag", size: 25, importance: 95 },
                { id: "n1", label: "@major_influencer", type: "account", size: 20, importance: 85 },
                { id: "n2", label: "@news_outlet", type: "account", size: 18, importance: 80 },
                { id: "n3", label: "@celebrity", type: "account", size: 17, importance: 75 },
                { id: "n4", label: "#related_tag1", type: "hashtag", size: 15, importance: 70 },
                { id: "n5", label: "#related_tag2", type: "hashtag", size: 15, importance: 70 },
                { id: "n6", label: "@amplifier1", type: "account", size: 12, importance: 60 },
                { id: "n7", label: "@amplifier2", type: "account", size: 12, importance: 60 },
                { id: "n8", label: "@regular_user1", type: "account", size: 8, importance: 40 },
                { id: "n9", label: "@regular_user2", type: "account", size: 8, importance: 40 },
                { id: "n10", label: "@regular_user3", type: "account", size: 8, importance: 40 }
            ],
            edges: [
                { source: "n1", target: "central", weight: 9, type: "used_hashtag" },
                { source: "n2", target: "central", weight: 8, type: "used_hashtag" },
                { source: "n3", target: "central", weight: 8, type: "used_hashtag" },
                { source: "n6", target: "central", weight: 7, type: "used_hashtag" },
                { source: "n7", target: "central", weight: 7, type: "used_hashtag" },
                { source: "n8", target: "central", weight: 4, type: "used_hashtag" },
                { source: "n9", target: "central", weight: 4, type: "used_hashtag" },
                { source: "n10", target: "central", weight: 4, type: "used_hashtag" },
                { source: "central", target: "n4", weight: 6, type: "cooccurrence" },
                { source: "central", target: "n5", weight: 6, type: "cooccurrence" },
                { source: "n1", target: "n2", weight: 5, type: "mention" },
                { source: "n2", target: "n1", weight: 4, type: "mention" },
                { source: "n3", target: "n1", weight: 3, type: "mention" },
                { source: "n6", target: "n1", weight: 5, type: "mention" },
                { source: "n7", target: "n1", weight: 5, type: "mention" }
            ],
            clusters: [
                { id: "c1", name: "Major Amplifiers", nodes: ["n1", "n2", "n3"] },
                { id: "c2", name: "Secondary Amplifiers", nodes: ["n6", "n7"] },
                { id: "c3", name: "Regular Users", nodes: ["n8", "n9", "n10"] },
                { id: "c4", name: "Related Hashtags", nodes: ["n4", "n5"] }
            ],
            keyNodes: [
                {
                    id: "n1",
                    title: "Primary Amplifier",
                    description: "Account responsible for 35% of hashtag reach",
                    score: 90
                },
                {
                    id: "c1",
                    title: "Primary Amplification Group",
                    description: "Three accounts responsible for initial hashtag virality",
                    score: 85
                },
                {
                    id: "c2",
                    title: "Coordinated Amplification",
                    description: "Secondary group showing synchronized posting patterns",
                    score: 75
                }
            ]
        },
        sentiment: {
            average: 0.25,
            distribution: {
                "Positive": 45,
                "Neutral": 35,
                "Negative": 20
            },
            trend: [0.1, 0.2, 0.3, 0.2, 0.25, 0.3, 0.25, 0.3, 0.2, 0.25],
            keywords: [
                { word: "trending", score: 0.5, count: 245 },
                { word: "viral", score: 0.6, count: 180 },
                { word: "popular", score: 0.7, count: 156 },
                { word: "discussion", score: 0.3, count: 142 },
                { word: "debate", score: -0.1, count: 128 }
            ]
        },
        timeline: {
            dates: ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", 
                    "Day 6", "Day 7", "Day 8", "Day 9", "Day 10"],
            metrics: {
                posts: [85, 350, 780, 620, 450, 380, 320, 280, 230, 180],
                engagement: [3200, 24000, 52000, 48000, 32000, 26000, 22000, 18000, 15000, 12000],
                reach: [45000, 280000, 650000, 580000, 410000, 340000, 290000, 240000, 190000, 150000]
            },
            events: [
                {
                    date: "Day 1",
                    title: "Hashtag Creation",
                    description: "Hashtag first appears, used by @major_influencer in viral post"
                },
                {
                    date: "Day 3",
                    title: "Peak Usage",
                    description: "Hashtag reaches maximum usage with 780 posts in a single day"
                },
                {
                    date: "Day 5",
                    title: "Sentiment Shift",
                    description: "Content using hashtag begins to show more neutral/critical tone"
                }
            ]
        }
    },
    
    // Topic Analysis
    topic1: {
        meta: {
            id: "topic1",
            name: "Technology Topic Analysis",
            description: "Analysis of technology sector discussion and narrative trends",
            dataPoints: 3580
        },
        network: {
            image: null,
            nodes: [
                { id: "central", label: "Technology", type: "topic", size: 25, importance: 95 },
                { id: "n1", label: "AI", type: "subtopic", size: 22, importance: 90 },
                { id: "n2", label: "Cybersecurity", type: "subtopic", size: 20, importance: 85 },
                { id: "n3", label: "Cloud Computing", type: "subtopic", size: 18, importance: 80 },
                { id: "n4", label: "@tech_news", type: "account", size: 16, importance: 75 },
                { id: "n5", label: "@tech_analyst", type: "account", size: 16, importance: 75 },
                { id: "n6", label: "@corp_account1", type: "account", size: 14, importance: 70 },
                { id: "n7", label: "@corp_account2", type: "account", size: 14, importance: 70 },
                { id: "n8", label: "#innovation", type: "hashtag", size: 12, importance: 65 },
                { id: "n9", label: "#futuretech", type: "hashtag", size: 12, importance: 65 },
                { id: "n10", label: "Automation", type: "subtopic", size: 10, importance: 60 }
            ],
            edges: [
                { source: "central", target: "n1", weight: 9, type: "includes" },
                { source: "central", target: "n2", weight: 8, type: "includes" },
                { source: "central", target: "n3", weight: 8, type: "includes" },
                { source: "central", target: "n10", weight: 6, type: "includes" },
                { source: "n1", target: "n10", weight: 7, type: "related" },
                { source: "n4", target: "central", weight: 9, type: "discusses" },
                { source: "n5", target: "central", weight: 9, type: "discusses" },
                { source: "n4", target: "n1", weight: 7, type: "discusses" },
                { source: "n5", target: "n1", weight: 7, type: "discusses" },
                { source: "n6", target: "central", weight: 6, type: "discusses" },
                { source: "n7", target: "central", weight: 6, type: "discusses" },
                { source: "n6", target: "n3", weight: 8, type: "discusses" },
                { source: "n7", target: "n2", weight: 8, type: "discusses" },
                { source: "n8", target: "central", weight: 7, type: "associated" },
                { source: "n9", target: "central", weight: 7, type: "associated" },
                { source: "n8", target: "n1", weight: 8, type: "associated" }
            ],
            clusters: [
                { id: "c1", name: "Core Technology Topics", nodes: ["central", "n1", "n2", "n3", "n10"] },
                { id: "c2", name: "Media & Analysts", nodes: ["n4", "n5"] },
                { id: "c3", name: "Corporate Accounts", nodes: ["n6", "n7"] },
                { id: "c4", name: "Trending Hashtags", nodes: ["n8", "n9"] }
            ],
            keyNodes: [
                {
                    id: "n1",
                    title: "AI (Subtopic)",
                    description: "Dominant subtopic representing 42% of technology discussion",
                    score: 90
                },
                {
                    id: "c2",
                    title: "Media & Analyst Narrative",
                    description: "Group driving public perception of technology trends",
                    score: 85
                },
                {
                    id: "n4",
                    title: "@tech_news",
                    description: "Most influential content publisher on technology topics",
                    score: 80
                }
            ]
        },
        sentiment: {
            average: 0.45,
            distribution: {
                "Positive": 55,
                "Neutral": 30,
                "Negative": 15
            },
            trend: [0.4, 0.45, 0.5, 0.55, 0.4, 0.45, 0.5, 0.4, 0.35, 0.45],
            keywords: [
                { word: "innovation", score: 0.85, count: 320 },
                { word: "disruption", score: 0.2, count: 285 },
                { word: "advances", score: 0.8, count: 245 },
                { word: "concerns", score: -0.5, count: 180 },
                { word: "adoption", score: 0.6, count: 165 }
            ]
        },
        timeline: {
            dates: ["Q1 2022", "Q2 2022", "Q3 2022", "Q4 2022", "Q1 2023", 
                    "Q2 2023", "Q3 2023", "Q4 2023"],
            metrics: {
                posts: [2800, 3100, 3400, 3800, 4200, 4500, 4800, 5200],
                engagement: [185000, 210000, 230000, 260000, 290000, 320000, 350000, 380000],
                reach: [2200000, 2500000, 2800000, 3100000, 3500000, 3800000, 4200000, 4600000]
            },
            events: [
                {
                    date: "Q4 2022",
                    title: "AI Trend Emergence",
                    description: "AI subtopic becomes dominant, representing over 40% of technology discussion"
                },
                {
                    date: "Q2 2023",
                    title: "Sentiment Peak",
                    description: "Most positive sentiment period corresponding with major product launches"
                },
                {
                    date: "Q3 2023",
                    title: "Narrative Shift",
                    description: "Increasing discussion of ethical concerns and regulation"
                }
            ]
        }
    }
};

// Default dataset
let currentDataset = PRELOADED_DATA.user1; 