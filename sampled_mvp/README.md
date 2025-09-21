# README.md
# MAB System MVP

A simplified but powerful Multi-Armed Bandit system for A/B testing.

## Features

- **Thompson Sampling**: Statistically robust arm selection
- **Real-time Analytics**: Bayesian analysis with confidence intervals
- **Simple Dashboard**: Clean, intuitive interface
- **GTM Integration**: Easy website integration
- **User Management**: Secure authentication
- **Database Persistence**: PostgreSQL with proper indexing

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd mab-mvp
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Run with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Access**:
   - Dashboard: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Deploy to Render

1. **Connect GitHub repository** to Render
2. **Use render.yaml** for automatic configuration
3. **Database** will be created automatically
4. **Environment variables** will be generated

## GTM Integration

Add this script to your website via Google Tag Manager:

```javascript
<script>
(function() {
    var script = document.createElement('script');
    script.src = 'https://your-app.onrender.com/static/frontend/gtm/mab-script.js';
    script.async = true;
    document.head.appendChild(script);
})();
</script>
```

Mark your HTML elements:

```html
<h1 data-test="hero-title">Your headline</h1>
<button data-test="cta-primary">Your button</button>
```

## API Endpoints

### Public (No Auth)
- `POST /api/experiments/{id}/assign` - Assign user to variant
- `POST /api/experiments/{id}/convert` - Record conversion

### Private (Requires Auth)
- `GET /api/experiments` - List experiments
- `POST /api/experiments` - Create experiment
- `GET /api/experiments/{id}/analytics` - Get analytics

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FRONTEND      │    │   BACKEND        │    │   DATABASE      │
│                 │    │                  │    │                 │
│ - HTML/CSS/JS   │◄──►│ - FastAPI        │◄──►│ - PostgreSQL    │
│ - Tailwind      │    │ - Thompson       │    │ - Async drivers │
│ - Vanilla JS    │    │   Sampling       │    │ - Proper indexes│
│                 │    │ - JWT Auth       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Core Algorithm

The system uses **Thompson Sampling** for optimal traffic allocation:

1. **Beta Distribution**: Each variant maintains alpha (successes) and beta (failures) parameters
2. **Sampling**: For each user, sample conversion rates from each variant's beta distribution
3. **Selection**: Show variant with highest sampled rate
4. **Update**: Increment alpha on conversion, beta on no conversion
5. **Analysis**: Use Bayesian statistics for confidence intervals and recommendations

## Scaling Path

### Phase 1: MVP (Current)
- Single server deployment
- PostgreSQL database
- Basic Thompson Sampling
- Simple dashboard

### Phase 2: Growth ($1k+ MRR)
- Redis caching layer
- Background job processing
- Advanced analytics
- Multi-variate testing

### Phase 3: Scale ($10k+ MRR)
- Microservices architecture
- Kubernetes deployment
- Machine learning features
- Enterprise integrations

## Development

### Project Structure
```
mab-mvp/
├── backend/           # Python FastAPI backend
│   ├── main.py       # FastAPI app
│   ├── models.py     # Pydantic models
│   ├── database.py   # PostgreSQL manager
│   ├── thompson.py   # Core algorithm
│   ├── auth.py       # Authentication
│   └── utils.py      # Utilities
│
├── frontend/         # Static frontend
│   ├── index.html    # Dashboard
│   ├── login.html    # Authentication
│   └── assets/       # CSS/JS
│
├── migrations/       # Database migrations
│   └── 001_initial.sql
│
└── static/          # Served by FastAPI
    └── frontend/    # Copied frontend files
```

### Local Development Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python -c "
import asyncio
from backend.database import DatabaseManager
async def migrate():
    db = DatabaseManager()
    await db.initialize()
asyncio.run(migrate())
"

# Access database
docker-compose exec postgres psql -U mab_user -d mab_system

# Run tests
docker-compose exec web python -m pytest
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `JWT_SECRET` | JWT signing secret | Required |
| `ENV` | Environment (development/production) | production |
| `LOG_LEVEL` | Logging level | INFO |
| `PORT` | Server port | 8000 |

## Security

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: bcrypt with salt
- **SQL Injection Protection**: Parameterized queries
- **HTTPS**: Enforced in production
- **Rate Limiting**: Built-in request limiting

## Monitoring

### Health Check
- Endpoint: `GET /health`
- Checks: Database connectivity, system resources
- Used by: Render deployment, load balancers

### Logs
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR
- Includes: Request IDs, user context, performance metrics

## Troubleshooting

### Common Issues

**Database connection failed**:
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
docker-compose exec postgres pg_isready
```

**Frontend not loading**:
```bash
# Check static files are served
curl http://localhost:8000/static/frontend/index.html

# Verify file permissions
ls -la static/frontend/
```

**Authentication errors**:
```bash
# Verify JWT_SECRET is set
echo $JWT_SECRET

# Check token in browser storage
# Open DevTools > Application > Local Storage
```

## Performance

### Expected Performance (MVP)
- **Response Time**: <100ms for assignments
- **Throughput**: 1000+ requests/minute
- **Database**: 100+ concurrent connections
- **Memory Usage**: <512MB

### Optimization Tips
1. **Database**: Proper indexing on foreign keys
2. **Caching**: Cache experiment configs
3. **Connection Pooling**: Reuse database connections
4. **Static Files**: CDN for frontend assets

## Cost Estimation

### Render.com Pricing (Monthly)
- **Web Service**: $7 (Starter plan)
- **PostgreSQL**: $7 (Starter plan)
- **Total**: ~$14/month

### Scaling Costs
- **10k users/day**: $25/month
- **100k users/day**: $75/month
- **1M users/day**: $200/month

## Support

For issues and questions:
1. Check logs: `docker-compose logs`
2. Review troubleshooting guide above
3. Check GitHub issues
4. Contact: [your-email]
