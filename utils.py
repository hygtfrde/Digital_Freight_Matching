def pretty_print_order(order, indent=0):
    ind = " " * indent
    print(f"{ind}Order:")
    print(f"{ind}  Pickup: Location(lat={order.pickup.latitude}, lon={order.pickup.longitude})")
    print(f"{ind}  Dropoff: Location(lat={order.dropoff.latitude}, lon={order.dropoff.longitude})")
    print(f"{ind}  Cargo:")
    for pkg in order.cargo.packages:
        print(f"{ind}    Package:")
        print(f"{ind}      Volume: {pkg.volume}")
        print(f"{ind}      Weight: {pkg.weight}")
        print(f"{ind}      Type: {pkg.type.value}")
    if order.client:
        print(f"{ind}  Client: {order.client}")
    if order.contract_type:
        print(f"{ind}  Contract type: {order.contract_type}")


# get_capacity_after_drop

# is_within_km

# deviation_time_for_stop
