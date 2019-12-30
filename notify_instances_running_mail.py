################################################################################
# Name      : notify_instances_running_mail
# Outline   : AWS起動インスタンス通知スクリプト
# environ   : REGION_SES = "us-east-1"          #SES利用リージョン
#           : REGION_INSTANCE = "us-east-2"     #インスタンス利用リージョン
#           : SRC_MAIL = "test@example.com"     #送信元アドレス
#           : DST_MAIL = "test@example.com"     #宛先アドレス
#           : PJ_CD_UPPER = "AAA"               #プロジェクトコード（大文字）（メールタイトルに利用）
#           : ENV_CD = "dev"                    #環境名（日本語表記）（メールタイトルに利用）
# Parameter : none
# Update    :
#  Ver      Date        Name            Comment
#  1.0      2018/02/04  K.Y             Start Initial Coding
################################################################################
################################################################################
# パッケージインポート
################################################################################
import os
import boto3
import datetime

################################################################################
# 変数定義
################################################################################
# 環境変数を取得する
REGION_SES = os.environ['REGION_SES']
REGION_INSTANCE = os.environ['REGION_INSTANCE']
SRC_MAIL = os.environ['SRC_MAIL']
DST_MAIL = os.environ['DST_MAIL']
PJ_CD_UPPER = os.environ['PJ_CD_UPPER']
ENV_CD = os.environ['ENV_CD']

# 日付を取得する
# 現在時刻を取得
# グリニッジ標準時
gmttime_now = datetime.datetime.now()
# 日本時間（フォーマット変換後）
jstime_now = "{0:%Y年%m月%d日%H時}".format(gmttime_now + datetime.timedelta(hours=9))

# インスタンス情報（EC2）
ec2_instance_id_list = ['インスタンスID']
ec2_ip_list = ['IPアドレス']
ec2_instancetype_list = ['インスタンスタイプ']
ec2_tags_list = ['インスタンス名']

# インスタンス情報（RDS）
rds_instance_identifier_list = ['インスタンス識別子']
rds_security_groups_list = ['セキュリティグループ']
rds_parameter_groups_list = ['パラメータグループ']
rds_instance_class_list = ['インスタンスクラス']

################################################################################
# 関数 check_ec2_running
# 用途 起動しているec2の情報を取得する
# 引数 none
# 戻値 ec2_instance_id_list, ec2_ip_list, ec2_instancetype_list, ec2_tags_list
################################################################################
def check_ec2_running():
    ec2 = boto3.client('ec2', region_name=REGION_INSTANCE)
    describe_instances = ec2.describe_instances(
        # ステータスが"running"を抽出する
        Filters = [
            {
                'Name' : 'instance-state-name',
                'Values' : [
                    'running'
                ]
            }
        ]
    )
    for reservations in describe_instances['Reservations']:
        for instances in reservations['Instances']:
            # インスタンスID、IPアドレス、インスタンスタイプを取得する
            ec2_instance_id_list.append(instances['InstanceId'])
            ec2_ip_list.append(instances['PrivateIpAddress'])
            ec2_instancetype_list.append(instances['InstanceType'])
            # インスタンス名を取得する
            for tags in instances['Tags']:
                if tags['Key'] == 'Name':
                    ec2_tags_list.append(tags['Value'])

    return ec2_instance_id_list, ec2_ip_list, ec2_instancetype_list, ec2_tags_list

################################################################################
# 関数 check_rds_running
# 用途 起動しているrdsの情報を取得する
# 引数 none
# 戻値 rds_instance_identifier_list, rds_security_groups_list, rds_parameter_groups_list, rds_instance_class_list
################################################################################
def check_rds_running():
    rds = boto3.client('rds', region_name=REGION_INSTANCE)
    describe_db_instances = rds.describe_db_instances()['DBInstances']
    for dbinstances in describe_db_instances:
        rds_instance_status = dbinstances['DBInstanceStatus']
        # ステータスが"available"を抽出する
        if rds_instance_status == "available":
            # インスタンス識別子、セキュリティグループ、パラメータグループ、インスタンスクラスを取得する
            rds_instance_identifier_list.append(dbinstances['DBInstanceIdentifier'])
            rds_security_groups_list.append(dbinstances['VpcSecurityGroups'][0]['VpcSecurityGroupId'])
            rds_parameter_groups_list.append(dbinstances['DBParameterGroups'][0]['DBParameterGroupName'])
            rds_instance_class_list.append(dbinstances['DBInstanceClass'])

    return rds_instance_identifier_list, rds_security_groups_list, rds_parameter_groups_list, rds_instance_class_list

################################################################################
# 関数 mail_by_ses
# 用途 メール本文を作成する＋sesを用いてメール通知する
# 引数 ec2_instance_id_list, ec2_ip_list, ec2_instancetype_list, ec2_tags_list, rds_instance_identifier_list, rds_security_groups_list, rds_parameter_groups_list, rds_instance_class_list
# 戻値 実行結果
################################################################################
def mail_by_ses(ec2_instance_id_list, ec2_ip_list, ec2_instancetype_list, ec2_tags_list, rds_instance_identifier_list, rds_security_groups_list, rds_parameter_groups_list, rds_instance_class_list):
    # メール内容を作成する
    # メールタイトル
    subject =    "【" + PJ_CD_UPPER + "】【" + ENV_CD + "】AWS起動インスタンス通知" + "(" + jstime_now + ")"
    # メール本文(ec2情報)
    body_ec2 = ""
    for i in range(len(ec2_instance_id_list)):
        body_ec2 += ec2_tags_list[i]
        body_ec2 += " | "
        body_ec2 += ec2_instance_id_list[i]
        body_ec2 += " | "
        body_ec2 += ec2_ip_list[i]
        body_ec2 += " | "
        body_ec2 += ec2_instancetype_list[i]
        body_ec2 += "\n"
    # メール本文(rds情報)
    body_rds = ""
    for i in range(len(rds_instance_identifier_list)):
        body_rds += rds_instance_identifier_list[i]
        body_rds += " | "
        body_rds += rds_security_groups_list[i]
        body_rds += " | "
        body_rds += rds_parameter_groups_list[i]
        body_rds += " | "
        body_rds += rds_instance_class_list[i]
        body_rds += "\n"
    # メール本文
    body =  "お疲れ様です。"
    body += PJ_CD_UPPER
    body += "です。\n"
    body += "\n"
    body += ENV_CD
    body += "環境における現時点("
    body +=  str(jstime_now)
    body += ")の起動インスタンスは下記です。\n"
    body += "\n"
    body += "■EC2\n"
    body += body_ec2
    body += "\n"
    body += "■RDS\n"
    body += body_rds
    body += "\n"
    body += "詳細はAWSマネジメントコンソールをご確認下さい。\n"
    body += "\n"
    body += "以上、よろしくお願いいたします。\n"
    body += "\n"

    # sesを用いてメール通知する
    ses = boto3.client('ses', region_name=REGION_SES)
    response = ses.send_email(
        Source = SRC_MAIL,
        Destination = {
            'ToAddresses' : [
                DST_MAIL,
            ]
        },
        Message={
            'Subject' : {
                'Data' : subject,
            },
            'Body' : {
                'Text' : {
                    'Data' : body,
                },
            }
        }
    )
    return response

################################################################################
# ハンドラー関数
################################################################################
def lambda_handler(event, context):
    ec2_instance_id_list, ec2_ip_list, ec2_instancetype_list, ec2_tags_list = check_ec2_running()
    rds_instance_identifier_list, rds_security_groups_list, rds_parameter_groups_list, rds_instance_class_list = check_rds_running()
    r = mail_by_ses(ec2_instance_id_list, ec2_ip_list, ec2_instancetype_list, ec2_tags_list, rds_instance_identifier_list, rds_security_groups_list, rds_parameter_groups_list, rds_instance_class_list)
    return r