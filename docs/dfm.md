```python
========== DIGITAL FREIGHT MATCHING SYSTEM ==========

Business logic module using unified schemas from schemas.py
Maintains all original matching and pricing logic

User Input → Validation → Business Logic (DFM) → Database → Feedback
     ↑                                                        │
     └────────────────────────────────────────────────────────┘

+---------+     +---------+     +--------+     +-----------+
|  Client |-----| C_Order |-----| Cargo  |-----| Package   |
+---------+     +---------+     +--------+     +-----------+
      |             |             |               |
      |             |             |               |
      |        pickup/dropoff     |           type|
      |         Location          |               |
      |             |             |               |
      |             |             |               |
      +--------+    |             |               |
               |    |             |               |
           +--------+             |               |
           | Location|------------+               |
           +--------+                             |
                                                 \|/
                                           +--------------+
                                           |  CargoType   |
                                           +--------------+

+---------+     +-------+     +----------+     +-----------+
|  Truck  |-----| Route |-----| T_Order  |     | Location  |
+---------+     +-------+     +----------+     +-----------+

+-------------------+
|  PricingService   |
+-------------------+
| - routes          |
| - trucks          |
| - pending_orders  |
+-------------------+

```