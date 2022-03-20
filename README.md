## 介绍
一款监测腾讯云轻量应用服务器流量包使用情况,并根据配置进行警告和关机的Python脚本.
## 需求
1. 环境: Python3.
2. 包: tencentcloud-sdk-python,json,requests.
## 配置
1. ACCOUNT代表腾讯云API密钥,可多个.
2. QUOTA代表限额值,当使用流量超过总流量*限额就会警告和关机,1代表100%.
3. SCT_KEY代表Server酱Key.
