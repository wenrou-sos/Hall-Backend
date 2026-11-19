
local holder = ARGV[1]

local pwdpool_key = "list@roompwdpool"
local pwdpookidx_key = "var@pwdpoolidx"

if redis.call("exists", pwdpool_key) == 0 then
    return ""
end
if redis.call("exists", pwdpookidx_key) == 0 then
    return ""
end
local pwdpool_len = tonumber(redis.call("llen", pwdpool_key))
if pwdpool_len == 0 then
    return ""
end
local pwdpool_idx = tonumber(redis.call("get", pwdpookidx_key)) + 1
if pwdpool_idx >= pwdpool_len then
    pwdpool_idx = 0
end
redis.call("set", pwdpookidx_key, pwdpool_idx)
local pwd = redis.call("lindex", pwdpool_key, pwdpool_idx)
return pwd
