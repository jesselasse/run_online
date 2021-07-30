# -*- coding: utf-8 -*-
from input_ import *
from output import *
from solve import *
import json



def one_drive(input_data,vehicle_start_time, available_duration,show=False):
    '''一趟运算'''
    # global goods, ports, vehicles
    goods = Goods(input_data["orderList"])
    vehicles = Vehicles(input_data["carList"])
    # print(goods.get_total_demand(),vehicles.get_total_capacity())
    ports = Ports(goods.goods, input_data["timeMatrix"], input_data["distMatrix"], input_data["indexToId"])
    nodes = Nodes(vehicles.vehicles, goods, ports)

# 输入展示
    if show:
        print('货物信息：')
        goods_info = {'长': goods.goods.l, '宽': goods.goods.w, '高': goods.goods.h, '体积': goods.goods.v, '目标驿站': goods.goods.n_port}
        df = pd.DataFrame(goods_info)
        display(df)

        print('地点信息')
        ports_info = {'坐标x':ports.ports.pos_x,'坐标y':ports.ports.pos_y, '货物总体积':ports.ports.v_total}
        df = pd.DataFrame(ports_info)
        display(df)

        print('车辆信息：')
        cars_info = {'长': vehicles.vehicles.L, '宽': vehicles.vehicles.W, '高': vehicles.vehicles.H, '体积': vehicles.vehicles.capacity}
        df = pd.DataFrame(cars_info)
        display(df)

        # print(time_matrix)
        print()

# 求解
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(nodes.number, vehicles.number
                                           , 0)

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)
    solution = solve(nodes, vehicles,manager,routing,vehicle_start_time, available_duration)

# 输出展示
    if solution:
        result = get_result(nodes, goods, ports, vehicles, manager, routing, solution, show)
        # 画图需要坐标，不加最后两个参数也没关系
        # result = get_result(nodes, goods, ports, vehicles, manager, routing, solution, show, np.array(pos_x), np.array(pos_y))
        return result
    else:
        # print('no solution')
        return 0

def main(input_data,show=False):
    dfc=pd.DataFrame(input_data["carList"])
    code=0
    st=time.mktime(time.strptime(input_data['sendTimeStart'], "%Y-%m-%d %H:%M:%S"))
    et=time.mktime(time.strptime(input_data['sendTimeEnd'], "%Y-%m-%d %H:%M:%S"))
    available_duration=int(et-st) # 可用时间间隔
    vehicle_start_time=[0]*dfc.size # 车辆发车时间
    captotal=sum(dfc['carLength']*dfc['carWidth']*dfc['carHeight'])
    vt = 0
    i = 0
    j = 0
    dfo = pd.DataFrame(input_data['orderList'])
    origin_order=dfo.sort_values(by="gridSiteId").to_dict('records')
    each_result=[] #每趟运算的result都记录在里面
    for go in origin_order:
        vt += (go['orderLength']*go['orderWidth']*go['orderHeight'])
        if vt > 0.85*captotal:
            input_data["orderList"] = origin_order[j:i]
            print("趟数：",len(each_result)+1)
            rt = one_drive(input_data,vehicle_start_time,available_duration,show=show). 
            code = 11
            if not rt:
                if available_duration:
                    available_duration=0
                    code=112
                    rt = one_drive(input_data,vehicle_start_time,available_duration,show=show)
                else:
                    return 0
            each_result.append(rt)
            vehicle_start_time=pd.DataFrame(rt['carList'],columns=['returnTime'])['returnTime'].tolist()
            j = i
            vt=go['orderLength']*go['orderWidth']*go['orderHeight']
        i+=1
    print("趟数：", len(each_result) + 1)
    input_data["orderList"] = origin_order[j:i]
    rt=one_drive(input_data,vehicle_start_time, available_duration, show=show)
    if not rt:
        if available_duration:
            available_duration = 0
            if code==0:
                code=12
            else:
                code=112
            rt = one_drive(input_data, vehicle_start_time, available_duration, show=show)
        else:
            return 0
    each_result.append(rt)
    return code, whole_result(each_result)


if __name__ == '__main__':
    with open('request_am.txt','r') as file:
        str2 = file.read()
        input_data = json.loads(str2)
    print(main(input_data))
