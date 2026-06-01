import psycopg2
regions = ['us-east-1', 'us-west-1', 'us-west-2', 'eu-central-1', 'eu-west-1', 'eu-west-2', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 'sa-east-1', 'ca-central-1']
password = 'hswT6@UA9V/us7t'

for region in regions:
    print(f"Testing {region}...")
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password=password,
            host=f'aws-0-{region}.pooler.supabase.com',
            port='6543',
            connect_timeout=3
        )
        print(f"SUCCESS! Region is {region}")
        conn.close()
        break
    except Exception as e:
        pass
