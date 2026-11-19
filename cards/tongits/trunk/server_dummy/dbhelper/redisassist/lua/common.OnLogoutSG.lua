
local uuid = ARGV[1]

local data_key = "sha@data_"..uuid
local svr_id_field = "svr_id"
redis.call("hdel", data_key, svr_id_field)
local uuid2sid_key = "sha@uuid2sid"
redis.call("hdel", uuid2sid_key, uuid)
redis.call("publish", "db_savebase", uuid)

return 0