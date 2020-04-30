# Deployment Guide

This document describes the steps to undertake in order to deploy a functioning
instance of the Session Invalidation application.

The `deploy/` directory contains resources such as the cloudformation stack
templates that describe required infrastructure.  At present, the initiation
of the deployment of this infrastructure is handled through the AWS web UI.

## Deploying to AWS

1. Invoke [maws](https://github.com/mozilla-iam/mozilla-aws-cli-mozilla) to
   configure your shell with credentials granting you write access to the
   account you wish to dpeloy to.  In Mozilla's case, this is infosec-dev-admin
   or infosec-prod-admin.
2. Create an EC2 keypair by navigating to **Services -> EC2 -> Key pairs** and
   selecting **Create key pair**.  Name the key
   **SessionInvalidationEc2KeyPair** and leave the file format as **pem**.
3. Begin the creation of the cloudformation stack by navigating to
   **Services -> CloudFormation -> Create stack -> With new resources**.
4. Under **Specify template**, select **Upload a template file** and select
   `deploy/infra.yml` from your file system after clicking **Choose file**.
5. After clicking **Next**, provide the following two configuration options:
  1. For **Stack name**, supply **SessionInvalidationInfra**.
  2. For **KeyPair**, supply **SessionInvalidationEc2KeyPair**.
6. Click **Next** and provide some tags, such as the following:
  * owner <your name>
  * service session-invalidation
7. Review everything to check for mistakes and click **Create stack**.
