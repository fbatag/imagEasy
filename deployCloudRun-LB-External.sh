export PROJECT_ID=$(gcloud config get project)
echo $PROJECT_ID
export REGION=southamerica-east1
export APP_NAME=imag-easy
export SUPPORT_EMAIL=dev@fbatagin.altostrat.com
export USER_GROUP=gcp-devops@fbatagin.altostrat.com

gcloud services enable iam.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com # para o Cloud Run
gcloud services enable iap.googleapis.com 
gcloud services enable run.googleapis.com
#gcloud services enable vision.googleapis.com # para covnersão de pdf em texto - não usado atualmente

export UPLOAD_BUCKET=$APP_NAME-upload-$PROJECT_ID
gcloud storage buckets create $UPLOAD_BUCKET --location=$REGION
#gcloud storage buckets update gs://UPLOAD_BUCKET --lifecycle-file=bucket_lifecycle.json
gcloud storage buckets update gs://$UPLOAD_BUCKET --cors-file=bucket-cors.json
gcloud storage buckets describe gs://$UPLOAD_BUCKET --format="default(cors_config)" # Verificar se acatou

export PROCESSED_BUCKET=$APP_NAME-processed-$PROJECT_ID
gcloud storage buckets create $PROCESSED_BUCKET --location=$REGION
#gcloud storage buckets update gs://PROCESSED_BUCKET --lifecycle-file=bucket_lifecycle.json
gcloud storage buckets update gs://$PROCESSED_BUCKET --cors-file=bucket-cors.json
gcloud storage buckets describe gs://$PROCESSED_BUCKET --format="default(cors_config)" # Verificar se acatou

gcloud storage buckets notifications create gs://$UPLOAD_BUCKET --topic=$PROJECT_ID/topics/$APP_NAME-upload-topic --event-types=OBJECT_FINALIZE 

export SERVICE_ACCOUNT=$APP_NAME-sa
gcloud iam service-accounts create $SERVICE_ACCOUNT \
--display-name "ImagEasy Service Account" \
--project $PROJECT_ID

gcloud storage buckets add-iam-policy-binding gs://$UPLOAD_BUCKET \
--member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
--role=roles/storage.objectUser --project=$PROJECT_ID

gcloud storage buckets add-iam-policy-binding gs://$PROCESSED_BUCKET \
--member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
--role=roles/storage.objectUser --project=$PROJECT_ID

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
--role roles/eventarc.eventReceiver

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
--role roles/aiplatform.user

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
--role roles/serviceusage.serviceUsageConsumer

#deploy em Cloud Run (não é necessário yaml)
export SERVICE_NAME=$APP_NAME-ui
gcloud config set run/region $REGION
gcloud run deploy $SERVICE_NAME --region=$REGION --source ./UI --min-instances=1 --timeout=60m \
   --project=$PROJECT_ID --ingress=internal-and-cloud-load-balancing --no-allow-unauthenticated  --cpu-throttling --quiet \
    
# deploys seguintes (omitir o service account)
# --cpu-throttling (CPU not allways allocated) and -no-allow-unauthenticated are default

# Crie um NEG sem servidor para o app sem servidor para o Cloud Run (essa lina é em comum com TODOS LOAD BALANCERS)
gcloud compute network-endpoint-groups create $SERVICE_NAME-serverless-neg --region=$REGION \
       --network-endpoint-type=serverless --cloud-run-service=$SERVICE_NAME

# LOAD BALANCER - EXTERNO
gcloud compute addresses create $SERVICE_NAME-glb-ip --network-tier=PREMIUM --ip-version=IPV4 --global
export LB_IP_NUMBER=$(gcloud compute addresses describe $SERVICE_NAME-glb-ip --format="get(address)" --global)
echo $LB_IP_NUMBER

#Crie um serviço de back-end
gcloud compute backend-services create $SERVICE_NAME-backend-ext --load-balancing-scheme=EXTERNAL_MANAGED --global
# Adicione o NEG sem servidor como um back-end ao serviço de back-end
gcloud compute backend-services add-backend $SERVICE_NAME-backend-ext  --global \
       --network-endpoint-group=$SERVICE_NAME-serverless-neg   --network-endpoint-group-region=$REGION
# Cria o frontend (LB) HTTP-proxy (NÃO FUNCIONA COM O IAP QUE REQUER HTTPS)
#gcloud compute target-http-proxies create $SERVICE_NAME-http-proxy  --url-map=$SERVICE_NAME-glb
#gcloud compute forwarding-rules create $SERVICE_NAME-http-fw-rule  --address=$LB_IP_NUMBER --global --ports=80 \
#   --target-http-proxy=$SERVICE_NAME-http-proxy --load-balancing-scheme=EXTERNAL_MANAGED  --network-tier=PREMIUM 
# Cria o frontend (LB) HTTPS-proxy
gcloud compute ssl-certificates create $SERVICE_NAME-ssl-cert --domains $DOMAIN
# Crie o LB
gcloud compute url-maps create $SERVICE_NAME-glb --default-service $SERVICE_NAME-backend-ext
gcloud compute target-https-proxies create $SERVICE_NAME-https-proxy-glb --url-map=$SERVICE_NAME-glb --ssl-certificates=$SERVICE_NAME-ssl-cert
gcloud compute forwarding-rules create $SERVICE_NAME-https-fw-rule-glb --address=$LB_IP_NUMBER --global --ports=443 \
   --target-https-proxy=$SERVICE_NAME-https-proxy-glb --load-balancing-scheme=EXTERNAL_MANAGED --network-tier=PREMIUM 


# Configurar o IAP para o LB
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID | grep projectNumber | grep -Eo '[0-9]+')
echo $PROJECT_NUMBER
gcloud beta services identity create --service=iap.googleapis.com --project=$PROJECT_ID
gcloud run services add-iam-policy-binding $SERVICE_NAME --member=serviceAccount:service-$PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com  \
--role='roles/run.invoker' --region $REGION

gcloud iap oauth-brands create --application_title=$APP_NAME --support_email=$SUPPORT_EMAIL
gcloud iap oauth-clients create BRAND --display_name=$APP_NAME
gcloud iap web enable --resource-type=backend-services --service=$SERVICE_NAME-backend
    
# Usuário da aplicação = permissão no IAP    
gcloud projects add-iam-policy-binding $PROJECT_ID --member=group:$USER_GROUP --role=roles/iap.httpsResourceAccessor

# Escopo Global
gcloud compute backend-services update $SERVICE_NAME-backend --global --iap=enabled
# OU Escopo Regional
gcloud compute backend-services update $SERVICE_NAME-backend --region $REGION --iap=enabled
