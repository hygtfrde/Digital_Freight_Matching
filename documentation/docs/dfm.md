========== DIGITAL FREIGHT MATCHING SYSTEM (MODERNIZED) ==========

User Input → Validation (BusinessValidator) → Order Processing (OrderProcessor) → Database → Feedback
     ↑                                                              │
     └──────────────────────────────────────────────────────────────┘

+---------+     +---------+     +--------+     +-----------+
|  Client |-----| Order   |-----| Cargo  |-----| Package   |
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

+--------------------------+
| Validation / Business    |
| Validator                |
+--------------------------+
| - business rules         |
| - audits & compliance    |
+--------------------------+

+--------------------------+
| OrderProcessor           |
+--------------------------+
| - order validation       |
| - matching/assignment    |
| - capacity, proximity    |
| - time, compatibility    |
+--------------------------+

# (Optional future module)
# +--------------------------+
# | RouteOptimizer           |
# +--------------------------+
# | - profitability logic    |
# | - batching/optimization  |
# +--------------------------+