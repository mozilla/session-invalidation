BUCKET_NAME="session-invalidation-static-content"

for filename in $(ls static); do
  echo "Uploading $filename";
  aws s3 cp "static/$filename" "s3://$BUCKET_NAME/$filename";
done
