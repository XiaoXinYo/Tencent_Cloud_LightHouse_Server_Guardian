# -*- coding: utf-8 -*-
# Author: XiaoXinYo

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.lighthouse.v20200324 import lighthouse_client, models
import json
import requests

ACCOUNT = {
	'SecretId': 'SecretKey'
}
REGION = ['ap-beijing', 'ap-chengdu', 'ap-guangzhou', 'ap-hongkong', 'ap-nanjing', 'ap-shanghai', 'ap-singapore', 'ap-tokyo', 'eu-moscow', 'na-siliconvalley']
QUOTA = 0.95 # 限额值,1为100%
SCT_KEY = 'SCT_KEY'

class light_house:
	def __init__(self, SecretId, SecretKey, Region):
		self.secret_id = SecretId
		self.secret_key = SecretKey
		cred = credential.Credential(self.secret_id, self.secret_key)
		httpProfile = HttpProfile()
		httpProfile.endpoint = 'lighthouse.tencentcloudapi.com'
		
		clientProfile = ClientProfile()
		clientProfile.httpProfile = httpProfile
		self.client = lighthouse_client.LighthouseClient(cred, Region, clientProfile)
	
	def __split_dict(self, data, size):
		list_d = []
		dict_len = len(data)
		# 获取分组数
		while_count = dict_len // size + 1 if dict_len % size != 0 else dict_len / size
		split_start = 0
		split_end = size
		while(while_count > 0):
			# 把字典的键放到列表中,根据偏移量拆分字典
			list_d.append({k: data[k] for k in list(data.keys())[split_start:split_end]})
			split_start += size
			split_end += size
			while_count -= 1
		return list_d
	
	def __get_instances(self):
		request = models.DescribeInstancesRequest()
		parameter = {}
		request.from_json_string(json.dumps(parameter))
		request_d = self.client.DescribeInstances(request) 
		data = json.loads(request_d.to_json_string()).get('InstanceSet')
		instances = {}
		for data_count in data:
			instances[data_count.get('InstanceId')] = {
				'ip_address': data_count.get('PublicAddresses')[0]
			}
		self.instances = instances
	
	def __get_traffic_package(self):
		instances = self.__split_dict(self.instances, 100)
		parameter = {}
		parameter['InstanceSet'] = []
		parameter['Limit'] = 100
		for instances_count in instances:
			for instances_count_count in instances_count:
				parameter['InstanceSet'].append(instances_count_count)
			request = models.DescribeInstancesTrafficPackagesRequest()
			request.from_json_string(json.dumps(parameter))
			request_d = self.client.DescribeInstancesTrafficPackages(request) 
			traffic_package = json.loads(request_d.to_json_string()).get('InstanceTrafficPackageSet')
			for traffic_package_count in traffic_package:
				id_s = traffic_package_count.get('InstanceId')
				single_traffic_package = traffic_package_count.get('TrafficPackageSet')[0]
				self.instances[id_s]['total_traffic_package'] = single_traffic_package.get('TrafficPackageTotal')
				self.instances[id_s]['use_traffic_package'] = single_traffic_package.get('TrafficUsed')
				self.instances[id_s]['surplus_traffic_package'] = single_traffic_package.get('TrafficPackageRemaining')
		return 	self.instances
	
	def __shutdown(self):
		instances = self.__split_dict(self.limit_instances, 100)
		parameter = {}
		parameter['InstanceIds'] = []
		for instances_count in instances:
			for instances_count_count in instances_count:
				parameter['InstanceIds'].append(instances_count_count)
			request = models.StopInstancesRequest()
			request.from_json_string(json.dumps(parameter))
			request_d = self.client.StopInstances(request) 
		
	def check(self, quota):
		self.__get_instances()
		self.__get_traffic_package()
		limit_instances = self.instances.copy()
		for instances_count in self.instances:
			single_instances = self.instances.get(instances_count)
			if single_instances.get('use_traffic_package') < single_instances.get('total_traffic_package') * quota:
				del limit_instances[instances_count]
		self.limit_instances = limit_instances
		self.__shutdown()
		return limit_instances

# Sever酱推送
def sct_push(message):
	global SCT_KEY
	post_data = {
		'title': '腾讯云轻量应用服务器警告',
		'desp': message
	}
	requests.post('https://sctapi.ftqq.com/' + SCT_KEY + '.send', post_data)

def guardian():
	global ACCOUNT, REGION, QUOTA, CHECK_INTERVAL
	for account_count in ACCOUNT:
		for region_count in REGION:
			object_d = light_house(account_count, ACCOUNT.get(account_count), region_count)
			instances = object_d.check(QUOTA)
			if instances != {}:
				message = ''
				GB = 1024 * 1024 * 1024
				for instances_count in instances:
					single_instances = instances.get(instances_count)
					message += 'ID:' + instances_count + '\n\nIP地址:' + single_instances.get('ip_address') + '\n\n总共流量包:' + str(round(single_instances.get('total_traffic_package') / GB, 2)) + ' GB\n\n使用流量包:' + str(round(single_instances.get('use_traffic_package') / GB, 2)) + ' GB\n\n剩余流量包:' + str(round(single_instances.get('surplus_traffic_package') / GB, 2)) + ' GB\n\n'
				message += '以上实例流量包使用已达到限额,已执行关机命令.'
				sct_push(message)

if __name__ == '__main__':
	guardian()
