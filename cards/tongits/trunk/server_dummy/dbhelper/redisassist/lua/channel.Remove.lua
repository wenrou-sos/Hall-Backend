local chl = ARGV[1]

local chl_key = "sha@chl_"..chl
if redis.call("exists", chl_key) == 0 then
    return -1
end
redis.call("del", chl_key)
return 0