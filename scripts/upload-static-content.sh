BUCKET_NAME="session-invalidation-static-content-$BUCKET_SUFFIX"

for filename in $(ls static); do
  aws s3 cp "static/$filename" "s3://$BUCKET_NAME/$filename";
done
