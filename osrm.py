from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def create_data_model(routing_data,vehicle):
    data = {}
    data['distance_matrix'] = routing_data
    data['num_vehicles'] = vehicle
    data['depot'] = 0
    return data


def solve_routing(data):
    
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']),   
        data['num_vehicles'],
        data['depot']
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):       
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        
        index = routing.Start(0)
        route = []

        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))

        route.append(manager.IndexToNode(index))
    return route


def print_solution(manager, routing, solution):
    index = routing.Start(0)
    plan_output = 'Route for vehicle 0:\n'
    route_distance = 0                                     
    while not routing.IsEnd(index):
        plan_output += f' {manager.IndexToNode(index)} -> '
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += f'{manager.IndexToNode(index)}\n'
    print(plan_output)
    print(f'Total Distance: {route_distance} km')