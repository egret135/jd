# jd
京东订单抓取

```shell script
python jd.py -h

usage: jd.py [-h] -s START_TIME -e END_TIME -u USERNAME -p PASSWORD [-n BEGIN_END_DATE] [-a {1,2}] [-t {0,1,2}] [-b BINARY_LOCATION] [-d] [-c CALLBACK_URL]

optional arguments:
  -h, --help            show this help message and exit
  -s START_TIME, --start START_TIME
                        抓取订单起始日期，格式为：Y-m-d
  -e END_TIME, --end END_TIME
                        抓取订单结束日期，格式为：Y-m-d
  -u USERNAME, --username USERNAME
                        京东商家账号
  -p PASSWORD, --password PASSWORD
                        京东商家密码
  -n BEGIN_END_DATE, --begin-end-date BEGIN_END_DATE
                        begin_end_date
  -a {1,2}, --date-type {1,2}
                        日期类型：1-收款到账日期，2-账单日期
  -t {0,1,2}, --status {0,1,2}
                        收款状态，0-代收款，1-收款中，2-已收款
  -b BINARY_LOCATION, --binary-location BINARY_LOCATION
                        浏览器可执行文件路径
  -d, --headless        不开启浏览器执行程序
  -c CALLBACK_URL, --callback-url CALLBACK_URL
                        结果数据回调链接
```

```shell script
python jd.py -s 2021-03-09 -e 2021-03-19 -u 'username' -p 'password' -d -c 'https://www.baidu.com'
```