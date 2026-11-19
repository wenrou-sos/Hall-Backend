local chl = ARGV[1]

local chl_key = "sha@chl_"..chl
if redis.call("exists", chl_key) == 0 then
    return { -1, "" }
end
local d = redis.call("hgetall", chl_key)
return { 0, d }