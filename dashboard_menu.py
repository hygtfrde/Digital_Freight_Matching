"""
========== DASHBOARD MENU ==========

User Input → Validation → Business Logic (DFM) → Database → Feedback
     ↑                                                        │
     └────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    MAIN MENU                                │
│                 Digital Freight Matching System              │
├─────────────────────────────────────────────────────────────┤
│  1. 📦 Order Management                                     │
│  2. 🚛 Fleet Management                                     │
│  3. 🗺️  Route Management                                    │
│  4. 💰 Pricing & Matching                                   │
│  5. 👥 Client Management                                    │
│  6. 📊 Reports & Analytics                                  │
│  7. ⚙️  System Configuration                                │
│  8. 🔍 Quick Search                                         │
│  9. ❌ Exit                                                 │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬─────────────┐
        ▼                   ▼                   ▼             ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ...
│ 1. ORDER MGMT │   │ 2. FLEET MGMT │   │ 3. ROUTE MGMT │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ 1. List All   │   │ 1. List Trucks│   │ 1. List Routes│
│ 2. Add New    │   │ 2. Add Truck  │   │ 2. Add Route  │
│ 3. View Detail│   │ 3. Edit Truck │   │ 3. Edit Route │
│ 4. Edit Order │   │ 4. Delete     │   │ 4. Delete     │
│ 5. Delete     │   │ 5. View Loads │   │ 5. View Orders│
│ 6. Match Order│   │ 6. Utilization│   │ 6. Optimize   │
│ 7. Pending    │   │ 7. Maintenance│   │ 7. Path View  │
│ 0. Back       │   │ 0. Back       │   │ 0. Back       │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
   [SUB-MENUS]         [SUB-MENUS]         [SUB-MENUS]

┌─────────────────────────────────────────────────────────────┐
│                    4. PRICING & MATCHING                    │
├─────────────────────────────────────────────────────────────┤
│  1. 🎯 Auto-Match Orders (Run matching algorithm)           │
│  2. 📋 View Pending Orders                                  │
│  3. 🔄 Process Pending Queue                                │
│  4. 💵 Calculate Route Profitability                        │
│  5. 🆕 Create New Route from Pending                        │
│  6. 📊 Matching Statistics                                  │
│  7. ⚙️  Matching Criteria Settings                          │
│  0. 🔙 Back to Main Menu                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    6. REPORTS & ANALYTICS                   │
├─────────────────────────────────────────────────────────────┤
│  1. 📈 Daily Summary                                        │
│  2. 🚛 Fleet Utilization Report                             │
│  3. 💰 Profitability Analysis                               │
│  4. ⏱️  Route Efficiency Metrics                            │
│  5. 📦 Cargo Type Distribution                              │
│  6. 🗺️  Geographic Coverage Map                            │
│  7. 📊 Custom Report Builder                                │
│  0. 🔙 Back to Main Menu                                    │
└─────────────────────────────────────────────────────────────┘

"""

from dfm import (
    CargoType, Location, Package, Cargo, Order, Client,
    Truck, Route, PricingService
)
from typing import List



