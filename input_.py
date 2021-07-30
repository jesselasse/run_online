# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import json
from urllib.request import urlopen
import datetime, time

#优必选的
ak = '5paKs1FbBGysjcULXKUVdKddtI4aiGFc'
sk = 'aGCRyZCs2ZsGFfH5xaRysRnlF2OYBy3e'

# #蒋陈的
# ak = 'ay9RIwrCo53Ca5wkQfEA2LzUpPGRw4eB'
# sk = 'HguuzlKqamP5FZL6CupMZTc0NAn0W4yW'

#梅老师的
# ak = '32QO0VUOYEDH52qYtsQHbZh2CrfDue2U'
# sk = 0
# 货物类
class Goods():
    """货物类，包含所有货物的信息"""

    def __init__(self, goods_list):
        self.number = len(goods_list)
        id = np.zeros(self.number)
        center = np.zeros(self.number)
        d = np.zeros(self.number)
        l = np.zeros(self.number)
        w = np.zeros(self.number)
        h = np.zeros(self.number)
        cost4gdarc = [0] * self.number
        weight = [0]
        self.IndexToId = dict()
        for index, good in enumerate(goods_list):
            self.IndexToId[index] = good["id"]
            id[index] = good["id"]
            center[index] = good["centerId"]
            d[index] = good["gridSiteId"]
            l[index] = good["orderLength"]
            w[index] = good["orderWidth"]
            h[index] = good["orderHeight"]
        v = l*w*h
        self.goods = pd.DataFrame({"id": id,
                                   "center": center,
                                   "n_port": d,
                                   "l": l,
                                   'w': w,
                                   'h': h,
                                   "v": v,
                                   "weight": weight * self.number,
                                   'cost': cost4gdarc,
                                   'unavailable': [set()] * self.number  # 不可用车辆
                                   })

    def get_total_demand(self):
        return sum(self.goods["v"])


# 车辆类
class Vehicles():
    """车辆类，包含所有车辆的信息"""

    def __init__(self, cars_list,r0=0.9):
        self.number = len(cars_list)
        self.IndexToId = dict()
        l = np.zeros(self.number)
        w = np.zeros(self.number)
        h = np.zeros(self.number)
        cost4vdarc = [1] * self.number  # 与车辆和路径有关（如开某辆车单位时间/距离的成本）
        cost4v = [1] * self.number  # 与车辆有关路径无关（如车辆派遣成本）
        for index, car in enumerate(cars_list):
            l[index] = car["carLength"]
            w[index] = car["carWidth"]
            h[index] = car["carHeight"]
            self.IndexToId[index] = car["id"]
        v = r0*l*w*h
        self.vehicles = pd.DataFrame({'L': l,  # 长
                                      'W': w,  # 宽
                                      'H': h,  # 高
                                      'capacity': v,  # 容积
                                      'cost': cost4v,
                                      'costdarc': cost4vdarc
                                      })

    def get_total_capacity(self):
        return sum(self.vehicles['capacity'])


class Ports():
    """地点（驿站+分拣点）类"""

    def __init__(self, goods, time_matrix, dist_matrix,IndexToId):
        # self.center_number = len(center_list)
        # self.site_number = len(site_list)
        self.center_number = 0
        self.site_number = 0
        self.number = len(IndexToId)
        self.centerIdToIndex = dict()
        self.siteIdToIndex = dict()
        self.IndexToId = dict()
        for index in range(self.number):
            type = IndexToId[index]["type"]
            id = IndexToId[index]["id"]
            if type == 1:
                self.centerIdToIndex[id] = index
                self.center_number = self.center_number + 1
            elif type == 2:
                self.siteIdToIndex[id] = index
                self.site_number = self.site_number + 1
            self.IndexToId[index] = [IndexToId[index]["type"], IndexToId[index]["id"]]

        pos_x = [0]*self.number
        pos_y = [0]*self.number
        goodset, vforposts = self.get_goods_for_ports(goods)
        self.ports = pd.DataFrame({
            "goodset": goodset,
            'v_total': vforposts,
            'pos_x': pos_x,  # pos_x：经度
            'pos_y': pos_y})  # pos_y:维度
        self.time_matrix = np.array(time_matrix)
        self.dist_matrix = np.array(dist_matrix)
        # self.time_matrix = self.get_time_matrix()
        self.costdarc = self.dist_matrix

    def get_goods_for_ports(self, goods):
        goodset = [[]]  # 同一驿站货物集合， 长M+1，驿站j的货物集合为goodset[j] (j=1~M)，分拣点goodset[0]=[]
        vforposts = [0]  # 同一驿站货物总体积， 长M+1，驿站j的货物总体积：vforpost[j]，分拣点vforpost[0]=0
        for j in self.siteIdToIndex.keys():
            idx = goods[goods.n_port == j].index
            
            goodset.append(idx.tolist())  # 货物的index，不是id
            vforposts.append(goods.v[idx].sum())

        return goodset, vforposts

    def get_time_matrix(self):

        def send_request(origins, destinations, ak, sk):
            # print(origins, destinations)
            url_drive = r"http://api.map.baidu.com/routematrix/v2/driving?output=json&origins={0}&destinations={1}&tactics=11&ak={2}".format(
                origins, destinations, ak)
            # if sk:
            #     encodedStr = urllib.parse.quote(queryStr, safe="/:=&?#+!$,;'@()*[]")
            #
            #     # 在最后直接追加上yoursk
            #     rawStr = encodedStr + sk
            #
            #     # md5计算出的sn
            #     sn = hashlib.md5(urllib.parse.quote_plus(rawStr).encode("utf-8")).hexdigest()
            #     print(sn)
            #     urllib.parse.quote("http://api.map.baidu.com" + queryStr + "&sn=" + sn, safe="/:=&?#+!$,;'@()*[]")
            #     # url_drive = url_drive + "&sn={0}".format(sn)

            result_drive = json.loads(urlopen(url_drive).read())  # json转dict
            status_drive = result_drive['status']
            #     print('ak秘钥：{0}  获取驾车路线状态码status：{1}'.format(ak, status_drive))
            print(result_drive['message'])
            if status_drive == 0:  # 状态码为0：无异常
                return result_drive['result']
            elif status_drive == 302 or status_drive == 210 or status_drive == 201:  # 302:额度不足;210:IP验证未通过
                print('AK错误')
                raise IOError('百度api错误')
            elif status_drive == 401:
                return 401
            else:
                print(status_drive)
                print('请求错误')
                raise IOError('百度api错误')

        def build_time_matrix(result, num_pos):
            # print(len(result))
            k = 0
            time_matrix = np.empty((num_pos, num_pos), dtype=int)
            for i in range(num_pos):
                for j in range(num_pos):
                    # if i == j:
                    #     time_matrix[i, j] = 0
                    # else:
                    time_matrix[i, j] = result[k]['duration']['value']
                    k += 1

            return time_matrix


        max_elements = 50
        # Maximum number of rows that can be computed per request
        if self.number<=max_elements:
            max_rows = max_elements // self.number
            # num_pos = q * max_rows + r
            q, r = divmod(self.number, max_rows)

            location = ''
            for i in range(self.number):
                location += (str(self.ports.pos_y[i]) + ',' + str(self.ports.pos_x[i]) + '|')
            dests = location[:-1]
            result = []
            # Send q requests, originsning s rows per request.
            for i in range(q):
                origins = ''
                for j in range(i * max_rows, (i + 1) * max_rows):
                    origins += (str(self.ports.pos_y[j]) + ',' + str(self.ports.pos_x[j]) + '|')
                origins = origins[:-1]
                while True:
                    res=send_request(origins, dests, ak, sk)
                    if res != 401:
                        break
                result.extend(res)

            # Get the remaining remaining r rows, if necessary.
            if r > 0:
                origins = ''
                for j in range(q * max_rows, q * max_rows + r):
                    origins += (str(self.ports.pos_y[j]) + ',' + str(self.ports.pos_x[j]) + '|')
                origins = origins[:-1]
                while True:
                    res = send_request(origins, dests, ak, sk)
                    if res != 401:
                        break
                result.extend(res)
        else:
            max_rows=1
            max_line=50
            # num_pos = q * max_rows
            q = self.number
            # num_pos = p * max_line + r
            p, r = divmod(self.number, max_line)
            location = ''
            for i in range(self.number):
                location += (str(self.ports.pos_y[i]) + ',' + str(self.ports.pos_x[i]) + '|')
            dests = location[:-1]
            result = []
            # check p+1 lines
            destss = []
            for i in range(p):
                destss.append('')
                for j in range(i*max_line, (i + 1) * max_line):
                    destss[-1] += (str(self.ports.pos_y[j]) + ',' + str(self.ports.pos_x[j]) + '|')
                destss[-1] = destss[-1][:-1]
            if r > 0:
                destss.append('')
                for j in range(p * max_line, p * max_line + r):
                    destss[-1] += (str(self.ports.pos_y[j]) + ',' + str(self.ports.pos_x[j]) + '|')
                destss[-1] = destss[-1][:-1]
            # Send q requests
            for i in range(q):
                origins = ''
                for j in range(i * max_rows, (i + 1) * max_rows):
                    origins += (str(self.ports.pos_y[j]) + ',' + str(self.ports.pos_x[j]) + '|')
                origins = origins[:-1]
                for k in range(len(destss)):
                    while True:
                        res=send_request(origins, destss[k], ak, sk)
                        if res != 401:
                            break
                    result.extend(res)

        return build_time_matrix(result, self.number)


def unavailable_vehicle_for_goods(goods, vehicles):
    '''
    货物尺寸中任意一个维度超过某一车辆尺寸，则它不能被装在这量车内。
    对每个货物good(=goods.iloc[i])，与每辆车的尺寸相比较，找出放不下这个货物的车，记录在货物good.unavailable信息里。

    输入：goods: Goods类对象中的goods属性；vehicles：Vehicles类对象中的vehicles属性
    输出：无（更新goods里面货物信息）
    '''
    limit = {'l': vehicles.L.sort_values(), 'w': vehicles.W.sort_values(), 'h': vehicles.H.sort_values()}#从小到达排
    for _ in ['l', 'w', 'h']:
        for i in range(len(goods)):
            for index, val in limit[_].items():
                if goods[_][i] < val:
                    break
                else:
                    goods.unavailable[i].add(index)


class Nodes():
    """
    结点信息类，结点为VRP算法求解的基本单位，一个结点包括同一驿站的多个货物
    每个结点的属性里包括货物集合、驿站信息（所有货物都是要送到这个驿站的）、货物体积和、货物的最大尺寸、最晚送达时间、货物卸货时间和。
    """

    def __init__(self, vehicles, goods, ports, r1=0.2):
        unavailable_vehicle_for_goods(goods.goods, vehicles)
        vmax = r1 * min(vehicles.capacity)  # 一个结点最大体积，自定义r1
        self.center_number = ports.center_number
        self.site_number = ports.site_number
        self.goods_number = goods.number
        self.nodes = pd.DataFrame([[0, [], 0, set(), 0, 0]], columns=["n_port",  # 驿站编号,id转为index
                                                                            "goodset",  # 货物编号集合
                                                                            "v_total",  # 体积和
                                                                            'unavailable',
                                                                            "weight",
                                                                            'cost'])
        self.get_nodes(goods.goods, ports, vmax)
        self.number = len(self.nodes)
        # 计算time_matrix:复制行列
        a = self.nodes.n_port.tolist()
        time_matrix = ports.time_matrix[a, :][:, a]
        c_matrix=np.ones(time_matrix.shape,dtype=int)*15*60 #卸货时间：没到一个驿站停留15分钟
        c_matrix[time_matrix==0] = 0
        c_matrix[0,:]=0
        self.time_matrix = time_matrix+c_matrix
        self.costdarc = ports.costdarc[a, :][:, a]


    def get_nodes(self, goods, ports, vmax):
        """
        从输入数据生成结点集合：
        针对驿站生成结点，如果一个驿站的所有货物能被最小的一辆车装下，则此驿站（的所有货物）=一个结点；
        如果一个驿站里的货物不能被最小的一辆车装下，则此驿站=多个结点，每个结点包含这个驿站的一部分货物

        """
        jj = 1
        for j in range(self.center_number, self.site_number+self.center_number):      # 站点的index
            # 没有货物的就不加入了
            if not ports.ports.goodset[j]:
                continue
            vj = ports.ports.v_total[j]
            if vj > vmax:
                # divideto=vj//vmax
                vpart = 0
                gs_ = []
                unavailable = set()
                for i in ports.ports.goodset[j]:
                    if vpart + goods.v[i] > vmax:
                        weight = goods.weight[gs_].sum()
                        self.nodes.loc[jj] = [j, gs_, vpart, unavailable, weight, goods.cost[gs_].sum()]
                        jj += 1
                        vpart = 0
                        gs_ = []
                        unavailable = set()
                    vpart += goods.v[i]
                    gs_.append(i)
                    unavailable.update(goods.unavailable[i])
                weight = goods.weight[gs_].sum()
                self.nodes.loc[jj] = [j, gs_, vpart, unavailable, weight, goods.cost[gs_].sum()]
                jj += 1
            else:
                gs_ = ports.ports.goodset[j]
                weight = goods.weight[gs_].sum()
                unavailable = set()
                for i in gs_:
                    unavailable.update(goods.unavailable[i])
                #                 print(jj)
                self.nodes.loc[jj] = [j, gs_, vj, unavailable, weight, goods.cost[gs_].sum()]
                jj += 1
    def set_manager(self, manager):
        self.manager = manager
