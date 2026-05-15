Sari-Sari Store POS and Inventory Management System



Project Overview

Sari-Sari Store POS and Inventory Management System is a desktop and Android-ready application designed to modernize small retail store operations. It replaces traditional manual tracking with a digital system that handles sales, inventory, and reporting in real-time.

Built using the Kivy framework and SQLite database, the system provides a simple yet powerful interface tailored for sari-sari store owners to efficiently manage daily transactions and stock levels.

Features

Secure Authentication
Login system with credential validation and protection against unauthorized access.

Real-Time Dashboard
Displays total products, low-stock alerts, daily revenue, and profit overview.

Inventory Management

Add, update, and delete products
Track product price, cost, and stock levels
Real-time search functionality
Low stock warning system

Sales Processing System

Fast transaction handling
Automatic stock deduction after each sale
Profit calculation per transaction
Receipt-style computation output

Reports Module

View sales history
Track daily performance
Monitor revenue and profit trends

Settings Module

Change username and password securely
Credential verification before updates
Repository Structure
├── main.py           # Core application logic and screen control
├── database.py       # SQLite database functions and queries
├── inventory.kv      # UI layout and design (Kivy KV Language)
├── buildozer.spec    # Android build configuration
└── README.md         # Project documentation
