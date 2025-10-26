"""
Create Superset Dashboards

This script creates all dashboards for the Healthcare ETL Pipeline using Superset's REST API.

Usage:
    python superset/create_dashboards.py --dashboard [operational|financial|clinical|provider|medication|all]
    
Environment Variables:
    SUPERSET_URL: Superset URL (default: http://localhost:8088)
    SUPERSET_USERNAME: Superset admin username (default: admin)
    SUPERSET_PASSWORD: Superset admin password (default: admin)
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from superset_setup import SupersetConfigurator


class DashboardCreator(SupersetConfigurator):
    """Create Superset dashboards programmatically"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database_id = None
        self.dataset_ids = {}
    
    def initialize(self) -> bool:
        """Initialize connection and get database/dataset IDs"""
        if not self.test_connection():
            return False
        
        if not self.login():
            return False
        
        # Get database ID
        self.database_id = self.get_database_id()
        if not self.database_id:
            print("✗ Healthcare Warehouse database not found")
            print("  Run: python superset_setup.py --action setup")
            return False
        
        # Get dataset IDs
        self.dataset_ids = self._get_all_dataset_ids()
        if not self.dataset_ids:
            print("✗ No datasets found")
            print("  Run: python superset_setup.py --action setup-datasets")
            return False
        
        print(f"✓ Initialized with database ID {self.database_id}")
        print(f"✓ Found {len(self.dataset_ids)} datasets")
        return True
    
    def _get_all_dataset_ids(self) -> Dict[str, int]:
        """Get all dataset IDs"""
        try:
            response = self.session.get(f"{self.superset_url}/api/v1/dataset/")
            if response.status_code == 200:
                datasets = response.json().get('result', [])
                return {ds['table_name']: ds['id'] for ds in datasets}
            return {}
        except Exception as e:
            print(f"✗ Error getting dataset IDs: {str(e)}")
            return {}
    
    def create_chart(
        self,
        chart_name: str,
        viz_type: str,
        dataset_id: int,
        params: Dict,
        description: str = ""
    ) -> Optional[int]:
        """
        Create a chart in Superset
        
        Args:
            chart_name: Name of the chart
            viz_type: Visualization type (e.g., 'big_number', 'line', 'bar')
            dataset_id: Dataset ID to use
            params: Chart parameters/configuration
            description: Chart description
            
        Returns:
            int: Chart ID if successful, None otherwise
        """
        chart_config = {
            'slice_name': chart_name,
            'viz_type': viz_type,
            'datasource_id': dataset_id,
            'datasource_type': 'table',
            'params': json.dumps(params),
            'description': description
        }
        
        try:
            response = self.session.post(
                f"{self.superset_url}/api/v1/chart/",
                json=chart_config
            )
            
            if response.status_code == 201:
                chart_id = response.json().get('id')
                print(f"  ✓ Created chart: {chart_name} (ID: {chart_id})")
                return chart_id
            else:
                print(f"  ✗ Failed to create chart {chart_name}: {response.status_code}")
                print(f"    Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ✗ Error creating chart {chart_name}: {str(e)}")
            return None
    
    def create_dashboard(
        self,
        dashboard_title: str,
        description: str,
        chart_ids: List[int],
        position_json: Dict = None
    ) -> Optional[int]:
        """
        Create a dashboard in Superset
        
        Args:
            dashboard_title: Dashboard title
            description: Dashboard description
            chart_ids: List of chart IDs to include
            position_json: Dashboard layout configuration
            
        Returns:
            int: Dashboard ID if successful, None otherwise
        """
        # Default position if not provided
        if position_json is None:
            position_json = self._generate_default_layout(chart_ids)
        
        dashboard_config = {
            'dashboard_title': dashboard_title,
            'slug': dashboard_title.lower().replace(' ', '-'),
            'published': True,
            'json_metadata': json.dumps({
                'color_scheme': 'supersetColors',
                'label_colors': {},
                'shared_label_colors': {},
                'color_scheme_domain': []
            }),
            'position_json': json.dumps(position_json)
        }
        
        try:
            response = self.session.post(
                f"{self.superset_url}/api/v1/dashboard/",
                json=dashboard_config
            )
            
            if response.status_code == 201:
                dashboard_id = response.json().get('id')
                print(f"✓ Created dashboard: {dashboard_title} (ID: {dashboard_id})")
                
                # Add charts to dashboard
                for chart_id in chart_ids:
                    self._add_chart_to_dashboard(dashboard_id, chart_id)
                
                return dashboard_id
            else:
                print(f"✗ Failed to create dashboard: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Error creating dashboard: {str(e)}")
            return None
    
    def _add_chart_to_dashboard(self, dashboard_id: int, chart_id: int) -> bool:
        """Add a chart to a dashboard"""
        try:
            # Get current dashboard
            response = self.session.get(f"{self.superset_url}/api/v1/dashboard/{dashboard_id}")
            if response.status_code != 200:
                return False
            
            dashboard = response.json().get('result', {})
            slices = dashboard.get('slices', [])
            
            # Add chart if not already present
            if chart_id not in [s.get('id') for s in slices]:
                slices.append({'id': chart_id})
                
                # Update dashboard
                update_response = self.session.put(
                    f"{self.superset_url}/api/v1/dashboard/{dashboard_id}",
                    json={'slices': [s.get('id') for s in slices]}
                )
                
                return update_response.status_code in [200, 204]
            
            return True
            
        except Exception as e:
            print(f"  ⚠ Error adding chart to dashboard: {str(e)}")
            return False
    
    def _generate_default_layout(self, chart_ids: List[int]) -> Dict:
        """Generate a default dashboard layout"""
        # Simple grid layout - 2 columns
        layout = {}
        row = 0
        col = 0
        
        for i, chart_id in enumerate(chart_ids):
            layout[f"CHART-{chart_id}"] = {
                "type": "CHART",
                "id": chart_id,
                "children": [],
                "meta": {
                    "width": 6,
                    "height": 50,
                    "chartId": chart_id
                }
            }
            
            col += 6
            if col >= 12:
                col = 0
                row += 50
        
        return layout
    
    def create_operational_overview_dashboard(self) -> Optional[int]:
        """Create Operational Overview Dashboard"""
        print("\nCreating Operational Overview Dashboard...")
        
        dataset_id = self.dataset_ids.get('fact_encounter')
        if not dataset_id:
            print("✗ fact_encounter dataset not found")
            return None
        
        chart_ids = []
        
        # Chart 1: Total Patients (Big Number)
        chart_id = self.create_chart(
            chart_name="Total Patients",
            viz_type="big_number_total",
            dataset_id=dataset_id,
            params={
                "metric": "count_distinct__patient_key",
                "adhoc_filters": [],
                "header_font_size": 0.3,
                "subheader_font_size": 0.15,
                "y_axis_format": ",d"
            },
            description="Total unique patients"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Chart 2: Total Encounters (Big Number)
        chart_id = self.create_chart(
            chart_name="Total Encounters",
            viz_type="big_number_total",
            dataset_id=dataset_id,
            params={
                "metric": "count",
                "adhoc_filters": [],
                "header_font_size": 0.3,
                "subheader_font_size": 0.15,
                "y_axis_format": ",d"
            },
            description="Total encounters"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Chart 3: Total Providers (Big Number)
        chart_id = self.create_chart(
            chart_name="Total Providers",
            viz_type="big_number_total",
            dataset_id=dataset_id,
            params={
                "metric": "count_distinct__provider_key",
                "adhoc_filters": [],
                "header_font_size": 0.3,
                "subheader_font_size": 0.15,
                "y_axis_format": ",d"
            },
            description="Active providers"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Chart 4: Top 10 Departments (Bar Chart)
        chart_id = self.create_chart(
            chart_name="Top 10 Departments by Patient Volume",
            viz_type="dist_bar",
            dataset_id=dataset_id,
            params={
                "metrics": ["count_distinct__patient_key"],
                "groupby": ["department"],
                "row_limit": 10,
                "order_desc": True,
                "show_legend": False,
                "show_bar_value": True,
                "bar_stacked": False
            },
            description="Top 10 departments by patient volume"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Chart 5: Visit Type Distribution (Pie Chart)
        chart_id = self.create_chart(
            chart_name="Visit Type Distribution",
            viz_type="pie",
            dataset_id=dataset_id,
            params={
                "metric": "count",
                "groupby": ["visit_type"],
                "show_labels": True,
                "show_legend": True,
                "donut": False,
                "show_labels_threshold": 5
            },
            description="Distribution of visit types"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Create dashboard
        if chart_ids:
            dashboard_id = self.create_dashboard(
                dashboard_title="Operational Overview",
                description="Monitor daily hospital operations and patient flow",
                chart_ids=chart_ids
            )
            return dashboard_id
        
        return None
    
    def create_financial_analytics_dashboard(self) -> Optional[int]:
        """Create Financial Analytics Dashboard"""
        print("\nCreating Financial Analytics Dashboard...")
        
        dataset_id = self.dataset_ids.get('fact_billing')
        if not dataset_id:
            print("✗ fact_billing dataset not found")
            return None
        
        chart_ids = []
        
        # Chart 1: Total Billed (Big Number)
        chart_id = self.create_chart(
            chart_name="Total Billed Amount",
            viz_type="big_number_total",
            dataset_id=dataset_id,
            params={
                "metric": "sum__billed_amount",
                "adhoc_filters": [],
                "header_font_size": 0.3,
                "subheader_font_size": 0.15,
                "y_axis_format": "$,.2f"
            },
            description="Total billed amount"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Chart 2: Total Paid (Big Number)
        chart_id = self.create_chart(
            chart_name="Total Paid Amount",
            viz_type="big_number_total",
            dataset_id=dataset_id,
            params={
                "metric": "sum__paid_amount",
                "adhoc_filters": [],
                "header_font_size": 0.3,
                "subheader_font_size": 0.15,
                "y_axis_format": "$,.2f"
            },
            description="Total paid amount"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Chart 3: Collection Rate (Big Number)
        chart_id = self.create_chart(
            chart_name="Collection Rate",
            viz_type="big_number_total",
            dataset_id=dataset_id,
            params={
                "metric": "avg__collection_rate",
                "adhoc_filters": [],
                "header_font_size": 0.3,
                "subheader_font_size": 0.15,
                "y_axis_format": ".2f%"
            },
            description="Average collection rate"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Chart 4: Denial Rate (Big Number)
        chart_id = self.create_chart(
            chart_name="Denial Rate",
            viz_type="big_number_total",
            dataset_id=dataset_id,
            params={
                "metric": "avg__denial_rate",
                "adhoc_filters": [],
                "header_font_size": 0.3,
                "subheader_font_size": 0.15,
                "y_axis_format": ".2f%"
            },
            description="Average denial rate"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Chart 5: Revenue by Insurance Provider (Bar Chart)
        chart_id = self.create_chart(
            chart_name="Revenue by Insurance Provider",
            viz_type="dist_bar",
            dataset_id=dataset_id,
            params={
                "metrics": ["sum__billed_amount"],
                "groupby": ["insurance_provider"],
                "row_limit": 10,
                "order_desc": True,
                "show_legend": False,
                "show_bar_value": True,
                "bar_stacked": False,
                "y_axis_format": "$,.0f"
            },
            description="Top 10 insurance providers by revenue"
        )
        if chart_id:
            chart_ids.append(chart_id)
        
        # Create dashboard
        if chart_ids:
            dashboard_id = self.create_dashboard(
                dashboard_title="Financial Analytics",
                description="Track revenue, payments, and claim denials",
                chart_ids=chart_ids
            )
            return dashboard_id
        
        return None
    
    def create_clinical_insights_dashboard(self) -> Optional[int]:
        """Create Clinical Insights Dashboard"""
        print("\nCreating Clinical Insights Dashboard...")
        print("  Note: This dashboard requires custom SQL queries")
        print("  Please create manually using the specifications in superset/dashboards/dashboard_specifications.md")
        return None
    
    def create_provider_performance_dashboard(self) -> Optional[int]:
        """Create Provider Performance Dashboard"""
        print("\nCreating Provider Performance Dashboard...")
        print("  Note: This dashboard requires custom SQL queries")
        print("  Please create manually using the specifications in superset/dashboards/dashboard_specifications.md")
        return None
    
    def create_medication_analysis_dashboard(self) -> Optional[int]:
        """Create Medication Analysis Dashboard"""
        print("\nCreating Medication Analysis Dashboard...")
        print("  Note: This dashboard requires medication data which may not be in the current schema")
        print("  Please create manually using the specifications in superset/dashboards/dashboard_specifications.md")
        return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Create Superset Dashboards for Healthcare ETL Pipeline'
    )
    parser.add_argument(
        '--dashboard',
        choices=['operational', 'financial', 'clinical', 'provider', 'medication', 'all'],
        default='all',
        help='Dashboard to create (default: all)'
    )
    parser.add_argument(
        '--superset-url',
        help='Superset URL (default: http://localhost:8088)'
    )
    parser.add_argument(
        '--username',
        help='Superset admin username (default: admin)'
    )
    parser.add_argument(
        '--password',
        help='Superset admin password (default: admin)'
    )
    
    args = parser.parse_args()
    
    # Create dashboard creator
    creator = DashboardCreator(
        superset_url=args.superset_url,
        username=args.username,
        password=args.password
    )
    
    # Initialize
    if not creator.initialize():
        print("\n✗ Initialization failed")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Creating Dashboards")
    print(f"{'='*60}")
    
    created_dashboards = []
    
    # Create dashboards based on selection
    if args.dashboard in ['operational', 'all']:
        dashboard_id = creator.create_operational_overview_dashboard()
        if dashboard_id:
            created_dashboards.append(('Operational Overview', dashboard_id))
    
    if args.dashboard in ['financial', 'all']:
        dashboard_id = creator.create_financial_analytics_dashboard()
        if dashboard_id:
            created_dashboards.append(('Financial Analytics', dashboard_id))
    
    if args.dashboard in ['clinical', 'all']:
        creator.create_clinical_insights_dashboard()
    
    if args.dashboard in ['provider', 'all']:
        creator.create_provider_performance_dashboard()
    
    if args.dashboard in ['medication', 'all']:
        creator.create_medication_analysis_dashboard()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Dashboard Creation Summary")
    print(f"{'='*60}")
    
    if created_dashboards:
        print(f"\n✓ Created {len(created_dashboards)} dashboard(s):")
        for name, dash_id in created_dashboards:
            print(f"  - {name} (ID: {dash_id})")
            print(f"    URL: {creator.superset_url}/superset/dashboard/{dash_id}/")
    else:
        print("\n⚠ No dashboards were created programmatically")
    
    print(f"\nNote: Some dashboards require manual creation due to complex SQL queries.")
    print(f"Please refer to: superset/dashboards/dashboard_specifications.md")
    print(f"\nAccess Superset at: {creator.superset_url}")
    print()


if __name__ == '__main__':
    main()
