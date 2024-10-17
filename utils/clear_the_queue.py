import redis


r = redis.StrictRedis(host='localhost', port=6379, db=0)

#清空队列
r.delete('b-depth') 