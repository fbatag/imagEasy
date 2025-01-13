export PROJECT_ID=$(gcloud config get project)
echo $PROJECT_ID
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID | grep projectNumber | grep -Eo '[0-9]+')
echo $PROJECT_NUMBER
export REGION=southamerica-east1
export APP_NAME=imageasy
export SERVICE_ACCOUNT=$APP_NAME-sa

export UPLOAD_BUCKET=$APP_NAME-upload-$PROJECT_ID
export PROCESSED_BUCKET=$APP_NAME-processed-$PROJECT_ID
export RESULT_BUCKET=$APP_NAME-result-$PROJECT_ID

export DOMAIN=$APP_NAME.fbatagin.demo.altostrat.com
export SERVICE_NAME_UI=$APP_NAME-ui
export SERVICE_NAME_PRC=$APP_NAME-processor

export SUPPORT_EMAIL=dev@fbatagin.altostrat.com
export USER_GROUP=gcp-devops@fbatagin.altostrat.com

gcloud services enable iam.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com # para o Cloud Run
gcloud services enable iap.googleapis.com 
gcloud services enable run.googleapis.com
#gcloud services enable vision.googleapis.com # para covnersão de pdf em texto - não usado atualmente

gcloud storage buckets create gs://$UPLOAD_BUCKET --location=$REGION
#gcloud storage buckets update gs://UPLOAD_BUCKET --lifecycle-file=bucket_lifecycle.json
gcloud storage buckets update gs://$UPLOAD_BUCKET --cors-file=bucket-cors.json
gcloud storage buckets describe gs://$UPLOAD_BUCKET --format="default(cors_config)" # Verificar se acatou

gcloud storage buckets create gs://$PROCESSED_BUCKET --location=$REGION
gcloud storage buckets create gs://$RESULT_BUCKET --location=$REGION

gcloud iam service-accounts create $SERVICE_ACCOUNT \
--display-name "ImagEasy Service Account" \
--project $PROJECT_ID

gcloud storage buckets add-iam-policy-binding gs://$UPLOAD_BUCKET \
--member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
--role=roles/storage.objectUser --project=$PROJECT_ID

gcloud storage buckets add-iam-policy-binding gs://$PROCESSED_BUCKET \
--member=serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
--role=roles/storage.objectUser --project=$PROJECT_ID

gcloud storage buckets add-iam-policy-binding gs://$RESULT_BUCKET \
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

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
--role roles/iam.serviceAccountTokenCreator

#deploy em Cloud Run (não é necessário yaml)
gcloud run deploy $SERVICE_NAME_UI --region=$REGION --source ./UI --min-instances=1 --timeout=5m \
   --service-account=$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
   --project=$PROJECT_ID --ingress=internal-and-cloud-load-balancing --no-allow-unauthenticated  --cpu-throttling --verbosity=debug 
   --quiet

# Criando o tópico pub/sub com o sink de eventos do bucket GCS 
gcloud storage buckets notifications create gs://$UPLOAD_BUCKET --topic=$PROJECT_ID/topics/$APP_NAME-upload-topic --event-types=OBJECT_FINALIZE 

gcloud functions deploy $SERVICE_NAME_PRC --region=$REGION --runtime python312 --source ./processor --timeout=9m --gen2 \
   --service-account=$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
   --project=$PROJECT_ID --ingress-settings=internal-only --no-allow-unauthenticated --verbosity=debug \
   --trigger-topic=$APP_NAME-upload-topic --entry-point=examUploadHandle \
   --trigger-service-account=$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com 
 #  --cpu-throttling não tem esse parâmetro no functions mesmo ele sendo, em última intância, uma CRun
 # na console do CRun, ele é chamado de billing - request ou instance based
 # na console do CFunctions ele não aparece, apesar de depois de deployado
 # Function é criado pro default como Request based, ms pdoe ser alterado com: gcloud run services update <service> --[no-]cpu-throttling

gcloud run services add-iam-policy-binding $SERVICE_NAME_PRC \
  --member="serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" --project=$PROJECT_ID

#gcloud run deploy $SERVICE_NAME_PRC --region=$REGION --source ./processor --min-instances=1 --timeout=60m \
#   --service-account=$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com \
#   --project=$PROJECT_ID --ingress=internal --no-allow-unauthenticated  --cpu-throttling --quiet 

# deploys seguintes (omitir o service account)
# --cpu-throttling (CPU not allways allocated) and -no-allow-unauthenticated are default

# LOAD BALANCER - EXTERNO
gcloud compute addresses create $SERVICE_NAME_UI-glb-ip --network-tier=PREMIUM --ip-version=IPV4 --global
export LB_IP_NUMBER=$(gcloud compute addresses describe $SERVICE_NAME_UI-glb-ip --format="get(address)" --global)
echo $LB_IP_NUMBER

# Crie um NEG sem servidor para o app sem servidor para o Cloud Run (essa lina é em comum com TODOS LOAD BALANCERS)
gcloud compute network-endpoint-groups create $SERVICE_NAME_UI-serverless-neg --region=$REGION \
       --network-endpoint-type=serverless --cloud-run-service=$SERVICE_NAME_UI
#Crie um serviço de back-end
gcloud compute backend-services create $SERVICE_NAME_UI-backend-ext --load-balancing-scheme=EXTERNAL_MANAGED --global 
# Adicione o NEG sem servidor como um back-end ao serviço de back-end
gcloud compute backend-services add-backend $SERVICE_NAME_UI-backend-ext  --global \
       --network-endpoint-group=$SERVICE_NAME_UI-serverless-neg --network-endpoint-group-region=$REGION

gcloud compute backend-services create $SERVICE_NAME_UI-backend-ext3 --load-balancing-scheme=EXTERNAL_MANAGED --global --protocol=HTTPS --port-name=http
gcloud compute backend-services add-backend $SERVICE_NAME_UI-backend-ext3 --global \
       --network-endpoint-group=$SERVICE_NAME_UI-serverless-neg --network-endpoint-group-region=$REGION

# Cria o frontend (LB) HTTP-proxy (NÃO FUNCIONA COM O IAP QUE REQUER HTTPS)
#gcloud compute target-http-proxies create $SERVICE_NAME_UI-http-proxy  --url-map=$SERVICE_NAME_UI-glb
#gcloud compute forwarding-rules create $SERVICE_NAME_UI-http-fw-rule  --address=$LB_IP_NUMBER --global --ports=80 \
#   --target-http-proxy=$SERVICE_NAME_UI-http-proxy --load-balancing-scheme=EXTERNAL_MANAGED  --network-tier=PREMIUM 
# Cria o frontend (LB) HTTPS-proxy
gcloud compute ssl-certificates create $SERVICE_NAME_UI-ssl-cert --domains $DOMAIN
# Crie o LB
gcloud compute url-maps create $SERVICE_NAME_UI-glb --default-service $SERVICE_NAME_UI-backend-ext
gcloud compute target-https-proxies create $SERVICE_NAME_UI-https-proxy-glb --url-map=$SERVICE_NAME_UI-glb --ssl-certificates=$SERVICE_NAME_UI-ssl-cert
gcloud compute forwarding-rules create $SERVICE_NAME_UI-https-fw-rule-glb --address=$LB_IP_NUMBER --global --ports=443 \
   --target-https-proxy=$SERVICE_NAME_UI-https-proxy-glb --load-balancing-scheme=EXTERNAL_MANAGED --network-tier=PREMIUM 


# Configurar o IAP para o LB
gcloud beta services identity create --service=iap.googleapis.com --project=$PROJECT_ID
gcloud run services add-iam-policy-binding $SERVICE_NAME_UI --member=serviceAccount:service-$PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com  \
--role='roles/run.invoker' --region $REGION

gcloud iap oauth-brands create --application_title=$APP_NAME --support_email=$SUPPORT_EMAIL
gcloud iap oauth-clients create BRAND --display_name=$APP_NAME
gcloud iap web enable --resource-type=backend-services --service=$SERVICE_NAME_UI-backend-ext
    
# Usuário da aplicação = permissão no IAP    
gcloud projects add-iam-policy-binding $PROJECT_ID --member=group:$USER_GROUP --role=roles/iap.httpsResourceAccessor

# Escopo Global
gcloud compute backend-services update $SERVICE_NAME_UI-backend-ext --global --iap=enabled
# OU Escopo Regional
gcloud compute backend-services update $SERVICE_NAME_UI-backend-ext --region $REGION --iap=enabled
