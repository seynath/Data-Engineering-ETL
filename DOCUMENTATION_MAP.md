# Documentation Map

## 📍 Where to Start

```
                    ┌─────────────────────┐
                    │   START_HERE.md     │ ← BEGIN HERE
                    │  (Master Index)     │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
    ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
    │ GETTING_STARTED  │  │    QUICK_    │  │     RUN_     │
    │      .md         │  │  REFERENCE   │  │   PIPELINE   │
    │                  │  │     .md      │  │     .md      │
    │ Complete Guide   │  │ Cheat Sheet  │  │   Detailed   │
    └──────────────────┘  └──────────────┘  └──────────────┘
```

## 🎯 Choose Your Path

### Path 1: Quick Start (5 minutes)

```
START_HERE.md → Run ./pipeline-cli.sh start → Done!
```

### Path 2: Guided Setup (15 minutes)

```
START_HERE.md → GETTING_STARTED.md → Run commands → Verify
```

### Path 3: Deep Dive (30 minutes)

```
START_HERE.md → GETTING_STARTED.md → RUN_PIPELINE.md → Customize
```

## 📚 Documentation Structure

### 🌟 Essential (Read These First)

#### [START_HERE.md](START_HERE.md)

**Purpose:** Master index and quick start
**When to read:** First thing, always
**Contains:**

- 30-second quick start
- Documentation index
- Tool overview
- Common tasks

#### [GETTING_STARTED.md](GETTING_STARTED.md)

**Purpose:** Complete beginner's guide
**When to read:** First time setup
**Contains:**

- Three ways to run
- Step-by-step instructions
- Verification steps
- Next steps guide

#### [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Purpose:** Command cheat sheet
**When to read:** Daily operations
**Contains:**

- All commands at a glance
- Access URLs
- Key directories
- Emergency commands

### 📖 Detailed Guides

#### [RUN_PIPELINE.md](RUN_PIPELINE.md)

**Purpose:** Comprehensive running instructions
**When to read:** Need detailed control
**Contains:**

- Manual step-by-step
- Troubleshooting guide
- Environment variables
- Advanced configuration

#### [STARTUP_CHECKLIST.md](STARTUP_CHECKLIST.md)

**Purpose:** Verification and validation
**When to read:** Ensuring everything works
**Contains:**

- Pre-flight checks
- Startup steps
- Success criteria
- Daily operations checklist

### 🔧 Troubleshooting

#### [FIXED_ISSUES.md](FIXED_ISSUES.md)

**Purpose:** Recent fixes and solutions
**When to read:** Having the same error
**Contains:**

- Problem description
- Root cause analysis
- Solution applied
- Verification steps

#### [SOLUTION_SUMMARY.md](SOLUTION_SUMMARY.md)

**Purpose:** Complete overview of fixes
**When to read:** Understanding what changed
**Contains:**

- What was fixed
- New tools created
- How to use everything
- Success checklist

### 📊 Project Documentation

#### [README.md](README.md)

**Purpose:** Project overview
**When to read:** Understanding the project
**Contains:**

- Architecture overview
- Project structure
- Component descriptions
- Full documentation links

## 🛠️ Tools & Scripts

### Main Tool: pipeline-cli.sh

```bash
./pipeline-cli.sh [command]
```

**Documentation:** See QUICK_REFERENCE.md or run `./pipeline-cli.sh help`

**Common Commands:**

- `start` - Start everything
- `stop` - Stop services
- `status` - Check health
- `logs` - View logs
- `trigger-dag` - Run pipeline
- `troubleshoot` - Diagnostics

### Supporting Scripts

#### start.sh

**Purpose:** Automated startup
**Documentation:** GETTING_STARTED.md
**Usage:** `./start.sh`

#### troubleshoot.sh

**Purpose:** Run diagnostics
**Documentation:** RUN_PIPELINE.md
**Usage:** `./troubleshoot.sh`

## 🎓 Learning Paths

### For Beginners

```
1. START_HERE.md (5 min)
2. Run ./pipeline-cli.sh start
3. GETTING_STARTED.md (10 min)
4. Explore Airflow UI
5. QUICK_REFERENCE.md (bookmark it)
```

### For Operators

```
1. QUICK_REFERENCE.md (daily use)
2. STARTUP_CHECKLIST.md (verification)
3. RUN_PIPELINE.md (troubleshooting)
4. Use ./pipeline-cli.sh commands
```

### For Developers

```
1. README.md (architecture)
2. RUN_PIPELINE.md (detailed setup)
3. airflow/dags/README.md (DAG structure)
4. dbt_project/README.md (transformations)
5. Customize and extend
```

## 🔍 Find Information By Topic

### Starting the Pipeline

- Quick: START_HERE.md
- Guided: GETTING_STARTED.md
- Manual: RUN_PIPELINE.md

### Commands & Operations

- Quick reference: QUICK_REFERENCE.md
- Detailed: RUN_PIPELINE.md
- Tool help: `./pipeline-cli.sh help`

### Troubleshooting

- Quick fix: QUICK_REFERENCE.md → Emergency Commands
- Diagnostics: Run `./pipeline-cli.sh troubleshoot`
- Common issues: FIXED_ISSUES.md
- Detailed: RUN_PIPELINE.md → Troubleshooting

### Verification

- Quick check: `./pipeline-cli.sh status`
- Complete: STARTUP_CHECKLIST.md
- Success criteria: SOLUTION_SUMMARY.md

### Configuration

- Environment: RUN_PIPELINE.md → Environment Variables
- Pipeline: config/pipeline_config.yaml
- Tables: config/silver_table_config.yaml

### Architecture & Design

- Overview: README.md
- DAG structure: airflow/dags/README.md
- dbt models: dbt_project/README.md

## 📋 Quick Decision Tree

```
Need to...

├─ Start the pipeline?
│  └─ Run: ./pipeline-cli.sh start
│     Read: START_HERE.md
│
├─ Check if it's working?
│  └─ Run: ./pipeline-cli.sh status
│     Read: STARTUP_CHECKLIST.md
│
├─ Find a command?
│  └─ Read: QUICK_REFERENCE.md
│     Or run: ./pipeline-cli.sh help
│
├─ Fix an issue?
│  └─ Run: ./pipeline-cli.sh troubleshoot
│     Read: FIXED_ISSUES.md or RUN_PIPELINE.md
│
├─ Learn how it works?
│  └─ Read: README.md
│     Then: airflow/dags/README.md
│
└─ Understand what changed?
   └─ Read: SOLUTION_SUMMARY.md
      Then: FIXED_ISSUES.md
```

## 🎯 By Role

### Data Engineer

**Primary docs:**

1. START_HERE.md
2. README.md
3. airflow/dags/README.md
4. dbt_project/README.md

**Daily use:**

- QUICK_REFERENCE.md
- ./pipeline-cli.sh

### DevOps / SRE

**Primary docs:**

1. RUN_PIPELINE.md
2. STARTUP_CHECKLIST.md
3. docker-compose.yml

**Daily use:**

- ./pipeline-cli.sh status
- ./pipeline-cli.sh logs
- ./pipeline-cli.sh troubleshoot

### Analyst / End User

**Primary docs:**

1. GETTING_STARTED.md
2. QUICK_REFERENCE.md

**Daily use:**

- Airflow UI (http://localhost:8080)
- Superset UI (http://localhost:8088)

## 📞 Getting Help

### Quick Help

```bash
./pipeline-cli.sh help
```

### Diagnostics

```bash
./pipeline-cli.sh troubleshoot
```

### Documentation

1. Check QUICK_REFERENCE.md for commands
2. Check FIXED_ISSUES.md for known issues
3. Check RUN_PIPELINE.md for detailed troubleshooting
4. Check logs: `./pipeline-cli.sh logs`

## 🗺️ File Locations

### Documentation Files (Root Directory)

```
START_HERE.md              ← Master index
GETTING_STARTED.md         ← Beginner guide
QUICK_REFERENCE.md         ← Command cheat sheet
RUN_PIPELINE.md            ← Detailed instructions
STARTUP_CHECKLIST.md       ← Verification guide
FIXED_ISSUES.md            ← Recent fixes
SOLUTION_SUMMARY.md        ← Complete overview
DOCUMENTATION_MAP.md       ← This file
README.md                  ← Project overview
```

### Scripts (Root Directory)

```
pipeline-cli.sh            ← Main CLI tool
start.sh                   ← Automated startup
troubleshoot.sh            ← Diagnostics
```

### Component Documentation

```
airflow/dags/README.md     ← DAG documentation
dbt_project/README.md      ← dbt documentation
config/README.md           ← Configuration guide
```

## 🚀 Ready to Start?

```bash
./pipeline-cli.sh start
```

Then explore the documentation as needed!

---

**Lost?** Go back to [START_HERE.md](START_HERE.md)
