// src/config.ts
const config = {
  api: {
    baseUrl: process.env.REACT_APP_API_URL || "https://ppwbzsy1bh.execute-api.us-west-2.amazonaws.com/prod"
  },
  buckets: {
    input: "optimo-input-files",
    output: "optimo-output-files"
  },
  region: "us-west-2"
};

export default config;
