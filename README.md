# OptimoV2 - AI-Powered Class Schedule Optimization

OptimoV2 is a production-ready class schedule optimization system that combines Mixed Integer Linear Programming (MILP) with Gemini AI to create optimal schedules while maximizing section utilization.

## 🌟 Key Features

- **Multi-Iteration Optimization**: Iteratively improves schedules using AI-driven insights
- **Real-Time Progress Tracking**: Monitor optimization progress with live updates
- **Comprehensive Analytics**: Visualize utilization distribution and teacher load
- **Serverless Architecture**: Scalable AWS infrastructure with pay-per-use pricing
- **User-Friendly Interface**: Modern React frontend with drag-and-drop file uploads

## 🚀 Live Demo

Access the production system: https://brettenf-uw.github.io/OptimoV2

## 📋 Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

### Basic Usage

1. **Prepare your CSV files**:
   - Period.csv
   - Sections_Information.csv
   - Student_Info.csv
   - Student_Preference_Info.csv
   - Teacher_Info.csv
   - Teacher_unavailability.csv

2. **Upload files** via the web interface
3. **Configure parameters** (iterations, utilization ranges)
4. **Submit job** and monitor progress
5. **Download results** when complete

## 🏗️ Architecture

- **Frontend**: React SPA hosted on GitHub Pages
- **API**: AWS API Gateway with Lambda functions
- **Compute**: AWS Batch with c5.24xlarge instances
- **Storage**: S3 for files, DynamoDB for metadata
- **AI**: Google Gemini API for optimization insights

See [OPTIMOV2_DEPLOYMENT_PLAN.md](OPTIMOV2_DEPLOYMENT_PLAN.md) for complete architecture details.

## 📁 Repository Structure

```
OptimoV2/
├── optimo-frontend/      # React frontend application
├── lambda/               # AWS Lambda functions
├── src/                  # Core optimization engine
│   ├── core/            # MILP solver implementation
│   ├── optimization/    # AI-driven optimization
│   └── pipeline/        # Orchestration logic
├── data/                # Sample data files
├── config/              # Configuration files
└── docs/                # Additional documentation
```

## 🔧 Technology Stack

- **Frontend**: React, TypeScript, Material-UI
- **Backend**: Python, AWS Lambda, AWS Batch
- **Optimization**: Gurobi MILP solver, Google Gemini AI
- **Infrastructure**: AWS (S3, DynamoDB, API Gateway, EventBridge)

## 📊 Performance

- Average optimization time: 8-15 minutes
- Handles 1000+ students, 100+ sections
- 85-95% section utilization achievement
- <200ms API response time

## 💰 Cost Estimate

~$223/month for moderate usage (1000 jobs)
- Compute: $200 (Spot instances)
- Storage: $10
- API/Lambda: $13

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Gurobi for academic license
- Google for Gemini API access
- AWS for cloud infrastructure

---

For detailed deployment instructions, see [OPTIMOV2_DEPLOYMENT_PLAN.md](OPTIMOV2_DEPLOYMENT_PLAN.md)