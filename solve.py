from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve(nodes, vehicles,manager,routing,vehicle_start_time, available_duration):
    '''算法运行：约束、目标、参数的定义'''

    # Create and register a time callback.
    def time_callback(from_index, to_index):
        """
        The time function we want is both transit time and service time.返回通过两结点间需要的时间
        """
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return nodes.time_matrix[from_node, to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Create demand callback
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return nodes.nodes.v_total[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)

    # 约束
    # Add capacity constraint
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        vehicles.vehicles.capacity.tolist(),  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    # 增加尺寸约束
    solver = routing.solver()
    for i in range(nodes.number):
        routing.VehicleVar(manager.NodeToIndex(i)).RemoveValues(nodes.nodes.unavailable[i])
    #         print(list(routing.VehicleVar(manager.NodeToIndex(i)).DomainIterator()))

    # Add Time Windows constraint.
    time = 'Time'
    routing.AddDimension(
        transit_callback_index,
        1000000,  # allow waiting time
        1000000,  # maximum time per vehicle
        False,  # start cumul to zero
        'Time')
    
    
    time_dimension = routing.GetDimensionOrDie(time)
    # Add time window constraints for each location except depot.
    if available_duration:
        for node_idx, node in nodes.nodes.iterrows():
            if node_idx == 0:
                continue
            index = manager.NodeToIndex(node_idx)
            time_dimension.CumulVar(index).SetRange(0, available_duration)
    # Add time window constraints for each vehicle start node.
    for vehicle_id in range(vehicles.number):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(vehicle_start_time[vehicle_id], max(vehicle_start_time[vehicle_id],available_duration))

    # Instantiate route start and end times to produce feasible times.
    for i in range(vehicles.number):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i)))
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(i)))

    #     # Create cost for goods in arc
    #     def cost_4good_callback(from_index):
    #         from_node = manager.IndexToNode(from_index)
    #         return nodes.cost[from_node]

    # 成本
    #     # Define cost of each arc.
    #     routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    # 车辆派遣成本(跟路径无关成本)
    for index, veh in vehicles.vehicles.iterrows():
        routing.SetFixedCostOfVehicle(int(veh.cost), index)

    # 跟路径有关成本（没考虑与货物相关）
    # keep transit callback alive
    cost_callback = []
    cost_callback_index_arr = []
    for index, veh in vehicles.vehicles.iterrows():
        def cost_callback_vehicle(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return nodes.costdarc[from_node, to_node] * veh.costdarc

        cost_callback.append(cost_callback_vehicle)
        cost_callback_index_arr.append(routing.RegisterTransitCallback(cost_callback[-1]))
        routing.SetArcCostEvaluatorOfVehicle(cost_callback_index_arr[-1], index)


    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
#     search_parameters.solution_limit = 10000000
#     search_parameters.time_limit.seconds = 10000000
#     search_parameters.lns_time_limit.seconds = 10000
#     print(search_parameters.lns_time_limit.seconds )

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING)
#    sl = nodes.number
#    print(sl)
    search_parameters.solution_limit = 80
    search_parameters.time_limit.FromSeconds(15)
    

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)
    return solution