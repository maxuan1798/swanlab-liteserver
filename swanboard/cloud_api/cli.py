#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SwanLab Cloud API CLI工具
提供命令行接口管理MySQL云端数据库
"""

import click
import os
from typing import Optional
from .mysql_config import MySQLConfig
from .mysql_connection import connect_cloud_db, disconnect_cloud_db, test_cloud_db_connection
from .cloud_service import CloudSyncManager
from .mysql_models import CLOUD_MODELS


@click.group()
@click.version_option()
def cli():
    """SwanLab Cloud API CLI - MySQL-based cloud synchronization management"""
    pass


@cli.command()
@click.option('--host', '-h', default='localhost', help='MySQL host')
@click.option('--port', '-p', default=3306, help='MySQL port')
@click.option('--user', '-u', default='root', help='MySQL user')
@click.option('--password', '-P', prompt=True, hide_input=True, help='MySQL password')
@click.option('--database', '-d', default='swanlab_cloud', help='MySQL database name')
def test_connection(host: str, port: int, user: str, password: str, database: str):
    """Test MySQL database connection"""
    config = MySQLConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

    click.echo(f"Testing connection to MySQL at {host}:{port}/{database}...")

    if connect_cloud_db(config):
        if test_cloud_db_connection():
            click.echo(click.style("✓ Connection successful!", fg='green'))
        else:
            click.echo(click.style("✗ Connection test failed", fg='red'))
        disconnect_cloud_db()
    else:
        click.echo(click.style("✗ Failed to connect to MySQL", fg='red'))


@cli.command()
@click.option('--host', '-h', default='localhost', help='MySQL host')
@click.option('--port', '-p', default=3306, help='MySQL port')
@click.option('--user', '-u', default='root', help='MySQL user')
@click.option('--password', '-P', prompt=True, hide_input=True, help='MySQL password')
@click.option('--database', '-d', default='swanlab_cloud', help='MySQL database name')
@click.confirmation_option(prompt='Are you sure you want to initialize the database?')
def init_db(host: str, port: int, user: str, password: str, database: str):
    """Initialize MySQL database tables"""
    config = MySQLConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

    click.echo(f"Initializing database {host}:{port}/{database}...")

    if connect_cloud_db(config):
        try:
            # Tables are automatically created by the connection manager
            click.echo(click.style("✓ Database initialized successfully!", fg='green'))
            click.echo(f"Created {len(CLOUD_MODELS)} tables:")
            for model in CLOUD_MODELS:
                click.echo(f"  - {model._meta.table_name}")
        except Exception as e:
            click.echo(click.style(f"✗ Failed to initialize database: {e}", fg='red'))
        finally:
            disconnect_cloud_db()
    else:
        click.echo(click.style("✗ Failed to connect to MySQL", fg='red'))


@cli.command()
@click.option('--workspace', '-w', default='default', help='Workspace name')
@click.option('--user-name', '-n', default='anonymous', help='User name')
def stats(workspace: str, user_name: str):
    """Show cloud sync statistics"""
    # Use environment variables for connection
    config = MySQLConfig.from_env()

    if not config.validate():
        click.echo(click.style("✗ Invalid MySQL configuration. Set environment variables:", fg='red'))
        click.echo("  MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
        return

    click.echo(f"Connecting to MySQL at {config.host}:{config.port}/{config.database}...")

    if connect_cloud_db(config):
        try:
            sync_manager = CloudSyncManager(workspace, user_name)
            stats_data = sync_manager.get_stats()

            if stats_data.get('connected'):
                click.echo(click.style("✓ Cloud sync active", fg='green'))
                click.echo(f"Workspace: {stats_data.get('workspace')}")
                click.echo(f"User: {stats_data.get('user')}")
                click.echo(f"Projects: {stats_data.get('projects', 0)}")
                click.echo(f"Experiments: {stats_data.get('experiments', 0)}")

                if stats_data.get('current_project'):
                    click.echo(f"Current Project: {stats_data.get('current_project')}")
                if stats_data.get('current_experiment'):
                    click.echo(f"Current Experiment: {stats_data.get('current_experiment')}")
            else:
                click.echo(click.style("✗ Cloud sync not active", fg='red'))
                if 'error' in stats_data:
                    click.echo(f"Error: {stats_data['error']}")

        except Exception as e:
            click.echo(click.style(f"✗ Failed to get stats: {e}", fg='red'))
        finally:
            disconnect_cloud_db()
    else:
        click.echo(click.style("✗ Failed to connect to MySQL", fg='red'))


@cli.command()
def env_example():
    """Show example environment variables configuration"""
    example_env = """
# SwanLab Cloud API Environment Variables Configuration

# Enable cloud synchronization
export SWANLAB_CLOUD_SYNC=true

# MySQL Database Configuration
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=swanlab_user
export MYSQL_PASSWORD=your_secure_password
export MYSQL_DATABASE=swanlab_cloud

# Cloud Workspace Configuration
export SWANLAB_WORKSPACE=my_workspace
export SWANLAB_USER=my_username

# Optional MySQL Configuration
export MYSQL_CHARSET=utf8mb4
export MYSQL_AUTOCOMMIT=true
export MYSQL_MAX_CONNECTIONS=20
export MYSQL_STALE_TIMEOUT=300
export MYSQL_TIMEOUT=20
    """
    click.echo(example_env.strip())


@cli.command()
@click.option('--workspace', '-w', required=True, help='Workspace name')
@click.option('--project', '-p', help='Project name filter')
def list_projects(workspace: str, project: Optional[str]):
    """List projects in workspace"""
    config = MySQLConfig.from_env()

    if not config.validate():
        click.echo(click.style("✗ Invalid MySQL configuration", fg='red'))
        return

    if connect_cloud_db(config):
        try:
            from .mysql_models import CloudProject

            query = CloudProject.select().where(CloudProject.workspace == workspace)
            if project:
                query = query.where(CloudProject.name.contains(project))

            projects = list(query)

            if projects:
                click.echo(f"Projects in workspace '{workspace}':")
                for proj in projects:
                    click.echo(f"  - {proj.name} ({proj.experiment_count} experiments)")
                    if proj.description:
                        click.echo(f"    Description: {proj.description}")
            else:
                click.echo(f"No projects found in workspace '{workspace}'")

        except Exception as e:
            click.echo(click.style(f"✗ Failed to list projects: {e}", fg='red'))
        finally:
            disconnect_cloud_db()
    else:
        click.echo(click.style("✗ Failed to connect to MySQL", fg='red'))


if __name__ == '__main__':
    cli()
