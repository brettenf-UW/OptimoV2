// AWS Configuration
// This file contains the AWS settings for the OptimoV2 application
// In production, these values would typically come from environment variables

const awsConfig = {
  region: "us-west-2",
  buckets: {
    input: "optimo-input-files-v2",
    output: "optimo-output-files"
  },
  api: {
    baseUrl: "https://3dbrbfl8f3.execute-api.us-west-2.amazonaws.com/prod"
  }
};

export default awsConfig;