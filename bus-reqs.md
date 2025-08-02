# DFM Business Requirements Analysis

## Current Business Situation

### Problem Context
- **Company**: Infinity and Beyond (family-owned trucking enterprise)
- **Location**: Atlanta, GA
- **Contract**: 4-year binding contract with Too-Big-To-Fail company
- **Assets**: 5 new specialized trucks
- **Coverage**: Routes spanning entire state of Georgia
- **Financial Status**: All 5 routes currently operating at loss ($-388.15 total daily loss)

### Constraints
1. Cannot cancel routes (4-year binding contract)
2. Heavy fines for early termination
3. Fixed rates based on cargo volume
4. Specialized trucks already purchased
5. Ongoing maintenance costs

## Business Solution: Digital Freight Matching (DFM)

### Core Business Model
Transform underutilized truck capacity into revenue by selling space to third-party shippers along existing routes.

### Revenue Optimization Strategy

#### Primary Revenue Stream
- Maintain existing contract obligations
- Add supplemental cargo from new clients
- Use same trucks, same routes, minimal additional costs

#### Key Business Rules

1. **Location Matching**
   - Must serve customers within 1km of existing route points
   - Minimizes deviation and additional fuel costs
   - Maintains schedule integrity

2. **Capacity Management**
   - Must account for existing contracted cargo
   - Optimize truck fill rate without exceeding capacity
   - Combine multiple small shipments when possible

3. **Time Management**
   - Each stop adds 15 minutes + deviation time
   - Total route cannot exceed 10 hours/day
   - Union break: 30 minutes after 4 hours (bonus requirement)

4. **Profitability Requirements**
   - Additional cargo must improve route profitability
   - New routes (from combined pending orders) MUST be profitable
   - Cost calculation based on Mr. Lightyear's spreadsheet

5. **Operational Constraints**
   - Routes must return to origin (round trip)
   - Some cargo types incompatible (hazmat + fragile, etc.)
   - Existing contract cargo takes priority

## Business Metrics & Goals

### Current State
| Route | Destination | Miles | Daily Loss | Time (hrs) |
|-------|-------------|-------|------------|------------|
| 1 | Ringgold | 202 | -$53.51 | 4.0 |
| 2 | Augusta | 189.2 | -$50.12 | 3.8 |
| 3 | Savannah | 496 | -$131.40 | 9.9 |
| 4 | Albany | 364 | -$96.43 | 7.3 |
| 5 | Columbus | 214 | -$56.69 | 4.3 |

### Target State
- Convert loss-making routes to profitable
- Maximize truck utilization
- Build sustainable third-party shipping business
- Maintain contract compliance

## Implementation Strategy

### Phase 1: Route Optimization
- Match incoming orders to existing routes
- Prioritize orders that:
  - Require minimal deviation
  - Improve route profitability most
  - Fill complementary cargo space

### Phase 2: Order Aggregation
- Collect unmatched orders
- Combine compatible cargo
- Create new profitable routes

### Phase 3: Dynamic Pricing
- Adjust pricing based on:
  - Route utilization
  - Deviation distance
  - Cargo type compatibility
  - Time constraints

## Risk Mitigation

### Operational Risks
- **Schedule delays**: 15-minute buffer per stop
- **Capacity overflow**: Real-time capacity tracking
- **Route deviation**: 1km maximum limit

### Business Risks
- **Contract violation**: Existing cargo always prioritized
- **Unprofitable additions**: Mandatory profitability check
- **Customer satisfaction**: Clear service boundaries

## Success Criteria

1. **Financial**: Each route achieves positive daily profit
2. **Operational**: Maintain 10-hour maximum route time
3. **Utilization**: Achieve >80% truck capacity usage
4. **Service**: Successfully match >60% of incoming orders

## Technical Implementation Needs

1. **Real-time Matching Engine**: Match orders to routes instantly
2. **Profitability Calculator**: Dynamic cost/revenue analysis
3. **Capacity Tracker**: Monitor available space
4. **Route Optimizer**: Calculate optimal stop sequences
5. **Order Queue**: Manage pending orders for batching