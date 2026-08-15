import os
import sys
import time
import platform
import psutil
import socket
import logging
from typing import Dict, Any, List
from sqlalchemy import text
from app.core.config import settings

logger = logging.getLogger("jarvis_system_environment")

async def get_os_info() -> Dict[str, Any]:
    """Detects real operating system and platform metadata."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "architecture": platform.architecture()[0],
        "node": platform.node(),
        "platform_str": platform.platform()
    }

async def get_cpu_info() -> Dict[str, Any]:
    """Fetches real CPU utilization and core metrics."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "physical_cores": psutil.cpu_count(logical=False) or 1,
        "logical_cores": psutil.cpu_count(logical=True) or 1,
        "load_avg": list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else [0.0, 0.0, 0.0]
    }

async def get_memory_info() -> Dict[str, Any]:
    """Fetches real RAM and Swap memory utilization."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_mb": round(mem.total / (1024 * 1024), 1),
        "available_mb": round(mem.available / (1024 * 1024), 1),
        "used_mb": round(mem.used / (1024 * 1024), 1),
        "percent_used": mem.percent,
        "swap_total_mb": round(swap.total / (1024 * 1024), 1),
        "swap_used_mb": round(swap.used / (1024 * 1024), 1)
    }

async def get_disk_info() -> Dict[str, Any]:
    """Fetches real filesystem partitions and disk space."""
    root_usage = psutil.disk_usage("/")
    return {
        "total_gb": round(root_usage.total / (1024**3), 2),
        "free_gb": round(root_usage.free / (1024**3), 2),
        "used_gb": round(root_usage.used / (1024**3), 2),
        "percent_used": root_usage.percent
    }

async def get_network_info() -> Dict[str, Any]:
    """Detects active network interfaces and IP addresses."""
    interfaces = {}
    try:
        addrs = psutil.net_if_addrs()
        for iface_name, iface_addrs in addrs.items():
            ip_list = []
            for addr in iface_addrs:
                if addr.family == socket.AF_INET:
                    ip_list.append(addr.address)
            if ip_list:
                interfaces[iface_name] = ip_list
    except Exception as e:
        logger.error(f"Error reading network addrs: {str(e)}")

    return {
        "hostname": socket.gethostname(),
        "interfaces": interfaces
    }

async def get_docker_info() -> Dict[str, Any]:
    """Detects if running inside Docker or checks Docker daemon availability."""
    in_docker = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")
    docker_sock_exists = os.path.exists("/var/run/docker.sock")

    return {
        "running_inside_container": in_docker,
        "docker_socket_available": docker_sock_exists,
        "status": "containerized" if in_docker else "host_native"
    }

async def get_postgres_health(db) -> Dict[str, Any]:
    """Performs an actual ping query against PostgreSQL / database engine."""
    try:
        start_time = time.time()
        await db.execute(text("SELECT 1"))
        duration_ms = (time.time() - start_time) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(duration_ms, 2),
            "engine": "active"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def get_redis_health() -> Dict[str, Any]:
    """Performs a real PING check against configured Redis URL."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        start = time.time()
        pong = await r.ping()
        duration_ms = (time.time() - start) * 1000
        await r.aclose()
        return {
            "status": "healthy" if pong else "unhealthy",
            "latency_ms": round(duration_ms, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": "Redis unavailable or connection refused",
            "details": str(e)
        }

async def get_process_list(limit: int = 15) -> List[Dict[str, Any]]:
    """Fetches real top active system processes."""
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "cpu_percent": info['cpu_percent'] or 0.0,
                    "memory_percent": round(info['memory_percent'] or 0.0, 2)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

    processes.sort(key=lambda p: p['cpu_percent'], reverse=True)
    return processes[:limit]

async def get_full_system_environment_report(db) -> Dict[str, Any]:
    """Compiles complete real system environment audit report."""
    os_info = await get_os_info()
    cpu_info = await get_cpu_info()
    mem_info = await get_memory_info()
    disk_info = await get_disk_info()
    net_info = await get_network_info()
    docker_info = await get_docker_info()
    pg_health = await get_postgres_health(db)
    redis_health = await get_redis_health()

    return {
        "status": "healthy" if pg_health["status"] == "healthy" else "degraded",
        "timestamp": time.time(),
        "os": os_info,
        "cpu": cpu_info,
        "memory": mem_info,
        "disk": disk_info,
        "network": net_info,
        "docker": docker_info,
        "postgresql": pg_health,
        "redis": redis_health
    }
