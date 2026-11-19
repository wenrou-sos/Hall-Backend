import jwt
#
# try:
#
secret = '-----BEGIN PUBLIC KEY-----\n' \
         'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4dGQ7bQK8LgILOdLsYzf' \
         'ZjkEAoQeVC/aqyc8GC6RX7dq/KvRAQAWPvkam8VQv4GK5T4ogklEKEvj5ISBamdD' \
         'Nq1n52TpxQwI2EqxSk7I9fKPKhRt4F8+2yETlYvye+2s6NeWJim0KBtOVrk0gWvE' \
         'Dgd6WOqJl/yt5WBISvILNyVg1qAAM8JeX6dRPosahRVDjA52G2X+Tip84wqwyRpU' \
         'lq2ybzcLh3zyhCitBOebiRWDQfG26EH9lTlJhll+p/Dg8vAXxJLIJ4SNLcqgFeZe' \
         '4OfHLgdzMvxXZJnPp/VgmkcpUdRotazKZumj6dBPcXI/XID4Z4Z3OM1KrZPJNdUh' \
         'xwIDAQAB' \
         '\n-----END PUBLIC KEY-----'
#     a = jwt.decode(
#         'eyJraWQiOiJlWGF1bm1MIiwiYWxnIjoiUlMyNTYifQ.eyJpc3MiOiJodHRwczovL2FwcGxlaWQuYXBwbGUuY29tIiwiYXVkIjoiY29tLnNsb3RzLmNhc2luby5qaW5zb25nIiwiZXhwIjoxNTkyMzY0Mzg5LCJpYXQiOjE1OTIzNjM3ODksInN1YiI6IjAwMTY2MC5lMmI2OWMwNmU5MGY0MDhlYWNlZjk4YjhiYjhiMWZkMC4wMzAxIiwiY19oYXNoIjoiaE9wWHl2RkMzeU9EN1k4eDFmaTdCdyIsImVtYWlsIjoicGxheWdlbXMuZGV2LmlvczFAaWNsb3VkLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjoidHJ1ZSIsImF1dGhfdGltZSI6MTU5MjM2Mzc4OSwibm9uY2Vfc3VwcG9ydGVkIjp0cnVlfQ.K6kKNnS52FznLjsk9J1CSBThN0uu7ZC79a_4oQ6JKFSss2Z4UnqXkah_zoySGj2D3sOuG113GKF69gZaNadpHaXHRjFudBnR-PO8K1g9g76S8FEJbhfF2TFtFCfYnu5biSyXbckvcfSIUXP-EjooDghx29JhQiUYw_ywBXOl9M_MWjqWr3TiJTd07UcyNO0IaL9Jc94_Ux8wLp08S2hjQUS2wb7HyjMnhfEJO8L_r2ONoKky59gLCvxyPK_A4I3UP84YAvZGTH9_a9NmUmGBKLrNh55Wzwx_WhFq9_Ac5K2eMwLDCAyMnTHKd12DIzFurqPNQUaJDo_u-USz9d4jvA',secret)
#     print(1)
# except Exception as e:
#
#     print(e)
encoded = 'eyJraWQiOiJlWGF1bm1MIiwiYWxnIjoiUlMyNTYifQ.eyJpc3MiOiJodHRwczovL2FwcGxlaWQuYXBwbGUuY29tIiwiYXVkIjoiY29tLnNsb3RzLmNhc2luby5qaW5zb25nIiwiZXhwIjoxNTkyMzY0Mzg5LCJpYXQiOjE1OTIzNjM3ODksInN1YiI6IjAwMTY2MC5lMmI2OWMwNmU5MGY0MDhlYWNlZjk4YjhiYjhiMWZkMC4wMzAxIiwiY19oYXNoIjoiaE9wWHl2RkMzeU9EN1k4eDFmaTdCdyIsImVtYWlsIjoicGxheWdlbXMuZGV2LmlvczFAaWNsb3VkLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjoidHJ1ZSIsImF1dGhfdGltZSI6MTU5MjM2Mzc4OSwibm9uY2Vfc3VwcG9ydGVkIjp0cnVlfQ.K6kKNnS52FznLjsk9J1CSBThN0uu7ZC79a_4oQ6JKFSss2Z4UnqXkah_zoySGj2D3sOuG113GKF69gZaNadpHaXHRjFudBnR-PO8K1g9g76S8FEJbhfF2TFtFCfYnu5biSyXbckvcfSIUXP-EjooDghx29JhQiUYw_ywBXOl9M_MWjqWr3TiJTd07UcyNO0IaL9Jc94_Ux8wLp08S2hjQUS2wb7HyjMnhfEJO8L_r2ONoKky59gLCvxyPK_A4I3UP84YAvZGTH9_a9NmUmGBKLrNh55Wzwx_WhFq9_Ac5K2eMwLDCAyMnTHKd12DIzFurqPNQUaJDo_u-USz9d4jvA'

# encoded = jwt.encode({'some': 'payload'}, 'secret', algorithm='HS256')
a = jwt.decode(encoded, secret, algorithms=['RS256'], options={'verify_exp': False},audience='com.slots.casino.jinsong')

print(a)
