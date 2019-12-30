################################################################################
# Name      : notify_billing_amount_mail.py
# Outline   : AWS請求額取得通知スクリプト
# environ   : REGION = "us-east-1"              #リージョン
#           : SRC_MAIL = "test@example.com"     #送信元アドレス
#           : DST_MAIL = "test@example.com"     #宛先アドレス
#           : PJ_CD = "AAA"                     #プロジェクトコード（メールタイトルに利用）
#           : ENV_CD = "dev"                    #環境名（メールタイトルに利用）
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
REGION = os.environ['REGION']
SRC_MAIL = os.environ['SRC_MAIL']
DST_MAIL = os.environ['DST_MAIL']
PJ_CD = os.environ['PJ_CD']
ENV_CD = os.environ['ENV_CD']

# 日付を取得する
# 今日を取得
today = datetime.datetime.today()
# 当月1日の値を出す
thismonth = datetime.datetime(today.year, today.month, 1)
# 前月末日の値を出す
lastmonth = thismonth + datetime.timedelta(days=-1)

################################################################################
# 関数 get_billing_amount_this_month
# 用途 今月（現時点）のAWS請求額を取得する
# 引数 none
# 戻値 cost_this_month, date_this_month
################################################################################
def get_billing_amount_this_month():
    cloudwatch = boto3.client('cloudwatch', region_name= REGION)
    get_metric_statistics = cloudwatch.get_metric_statistics(
        Namespace ='AWS/Billing',
        MetricName ='EstimatedCharges',
        Dimensions = [
            {
                'Name' : 'Currency',
                'Value' : 'USD'
                }
                ],
                StartTime = today - datetime.timedelta(days=1),
                EndTime = today,
                Period = 86400,
                Statistics = ['Maximum'])
    cost_this_month = get_metric_statistics['Datapoints'][0]['Maximum']
    date_this_month = get_metric_statistics['Datapoints'][0]['Timestamp'].strftime('%Y年%m月%d日')
    return cost_this_month, date_this_month

################################################################################
# 関数 get_billing_amount_last_month
# 用途 先月のAWS請求額を取得する
# 引数 none
# 戻値 cost_last_month
################################################################################
def get_billing_amount_last_month():
    cloudwatch = boto3.client('cloudwatch', region_name= REGION)
    get_metric_statistics = cloudwatch.get_metric_statistics(
        Namespace = 'AWS/Billing',
        MetricName = 'EstimatedCharges',
        Dimensions = [
            {
                'Name' : 'Currency',
                'Value' : 'USD'
                }
                ],
                StartTime = lastmonth - datetime.timedelta(days=1),
                EndTime = lastmonth,
                Period = 86400,
                Statistics = ['Maximum'])
    cost_last_month = get_metric_statistics['Datapoints'][0]['Maximum']
    return cost_last_month

################################################################################
# 関数 mail_by_ses
# 用途 メール本文を作成する＋sesを用いてメール通知する
# 引数 cost_this_month, date_this_month, cost_last_month
# 戻値 実行結果
################################################################################
def mail_by_ses(cost_this_month, date_this_month, cost_last_month):
    # メール本文を作成する
    subject =  "【" + PJ_CD + "】【" + ENV_CD + "】AWS請求額通知" + "(" + date_this_month + ")"
    body =  "お疲れ様です。"
    body += PJ_CD
    body += "です。\n"
    body += "\n"
    body += ENV_CD
    body += "環境における今月現時点("
    body +=  str(date_this_month)
    body += ")のAWS請求額は"
    body += str(cost_this_month)
    body += "ドルです。\n"
    body += "\n"
    body += "[参考]\n"
    body += "先月のAWS請求額(月額)は"
    body += str(cost_last_month)
    body += "ドルです。\n"
    body += "\n"
    body += "詳細はAWSマネジメントコンソール→請求ダッシュボードをご確認下さい"

    # sesを用いてメール通知する
    ses = boto3.client('ses', region_name=REGION)
    response = ses.send_email(
        Source = SRC_MAIL,
        Destination = {
            'ToAddresses' : [
                DST_MAIL,
            ]
        },
        Message = {
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
    cost_this_month, date_this_month = get_billing_amount_this_month()
    cost_last_month = get_billing_amount_last_month()
    r = mail_by_ses(cost_this_month, date_this_month, cost_last_month)
    return r