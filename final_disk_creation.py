#!/usr/bin/env python3
"""
最终磁盘创建脚本 - 从batch-243到batch-1000
创建剩余的758个虚拟磁盘，每个10GB
"""

import sys
import os
import time
from massive_disk_creator import MassiveDiskCreator

class FinalDiskCreator(MassiveDiskCreator):
    """最终磁盘创建器 - 从当前最高编号继续"""
    
    def __init__(self):
        super().__init__()
        
    def create_final_batch(self, start_num: int, end_num: int = 1000) -> dict:
        """创建从start_num到end_num的磁盘"""
        
        total_disks = end_num - start_num + 1
        print(f"🚀 最终磁盘创建任务")
        print(f"📊 磁盘范围: batch-{start_num:04d} 到 batch-{end_num:04d}")
        print(f"💾 每个大小: 10GB")
        print(f"🎯 总计: {total_disks}个磁盘")
        print("=" * 80)
        
        # 选择环境（使用自动选择，优先生产环境）
        env_id = self.env_creator.auto_select_environment("production")
        if not env_id:
            print("❌ 无法选择合适的环境")
            return {"success": False}
            
        # 验证环境
        if not self.env_creator.check_environment(env_id):
            print("❌ 环境验证失败")
            return {"success": False}
        
        start_time = time.time()
        results = []
        success_count = 0
        failed_count = 0
        
        for i in range(start_num, end_num + 1):
            disk_name = f"batch-{i:04d}"
            progress = i - start_num + 1
            print(f"\n📁 创建磁盘 {progress}/{total_disks}: {disk_name}")
            
            try:
                from smart_disk_creator import SmartDiskCreator
                disk_creator = SmartDiskCreator("admin", "Admin@123", "https://172.118.57.100")
                
                # 智能配置 - 修复版本
                config_result = disk_creator.generate_optimal_config(10, "standard")
                
                if not config_result["success"]:
                    print(f"❌ {disk_name} 配置失败: {config_result['error']}")
                    failed_count += 1
                    results.append({
                        'disk_name': disk_name,
                        'disk_num': i,
                        'success': False,
                        'error': config_result['error']
                    })
                    continue
                
                # 修改配置，使用正确的磁盘名称
                config = config_result["config"]
                config['name'] = disk_name
                
                # 创建磁盘
                print(f"🔧 创建配置: 大小=10GB, IOPS={config['iops']}, 带宽={config['bandwidth']}MB/s")
                
                from volumes import Volumes
                volumes = Volumes(disk_creator.audit, disk_creator.host)
                result = volumes.createDisk_vstor(**config)
                
                # 解析结果
                if isinstance(result, dict):
                    if 'data' in result and result['data'] and len(result['data']) > 0:
                        disk_info = result['data'][0]
                        print(f"✅ {disk_name} 创建成功! ID: {disk_info['id']}")
                        success_count += 1
                        results.append({
                            'disk_name': disk_name,
                            'disk_num': i,
                            'success': True,
                            'disk_id': disk_info['id']
                        })
                    elif 'errorMessage' in result and 'exist' in result['errorMessage'].lower():
                        print(f"⚠️ {disk_name} 已存在，跳过")
                        success_count += 1  # 算作成功，因为已经存在
                        results.append({
                            'disk_name': disk_name,
                            'disk_num': i,
                            'success': True,
                            'disk_id': 'existing',
                            'note': '已存在'
                        })
                    else:
                        print(f"❌ {disk_name} 创建失败: {result.get('errorMessage', '未知错误')}")
                        failed_count += 1
                        results.append({
                            'disk_name': disk_name,
                            'disk_num': i,
                            'success': False,
                            'error': result.get('errorMessage', '未知错误')
                        })
                else:
                    print(f"❌ {disk_name} 创建失败: 意外响应格式")
                    failed_count += 1
                    results.append({
                        'disk_name': disk_name,
                        'disk_num': i,
                        'success': False,
                        'error': '意外响应格式'
                    })
                
                # 每创建50个磁盘显示一次进度
                if progress % 50 == 0:
                    print(f"\n📊 进度报告 (已完成{progress}个磁盘):")
                    print(f"✅ 成功: {success_count}")
                    print(f"❌ 失败: {failed_count}")
                    print(f"📈 成功率: {success_count/progress*100:.1f}%")
                    print(f"💾 已创建容量: {success_count * 10}GB")
                
                # 添加延迟，避免API频率限制
                if i < end_num:
                    print("⏳ 等待1秒后继续...")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ {disk_name} 创建出错: {e}")
                failed_count += 1
                results.append({
                    'disk_name': disk_name,
                    'disk_num': i,
                    'success': False,
                    'error': str(e)
                })
        
        # 显示最终结果
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n" + "=" * 80)
        print(f"🎉 最终磁盘创建任务完成!")
        print("=" * 80)
        print(f"⏱️  总耗时: {duration/60:.1f} 分钟")
        print(f"📊 总磁盘数: {total_disks}个")
        print(f"✅ 成功创建: {success_count}个")
        print(f"❌ 创建失败: {failed_count}个")
        print(f"📈 成功率: {success_count/total_disks*100:.1f}%")
        print(f"💾 成功总容量: {success_count * 10}GB")
        print(f"🌐 目标环境: {self.env_creator.connection_info['name']}")
        
        # 显示失败的磁盘
        if failed_count > 0:
            print(f"\n❌ 失败的磁盘 (前10个):")
            failed_disks = [r for r in results if not r['success']][:10]
            for result in failed_disks:
                error_info = f" - {result.get('error', '未知错误')}"
                print(f"   {result['disk_name']}: 创建失败{error_info}")
            if failed_count > 10:
                print(f"   ... 还有 {failed_count - 10} 个磁盘失败")
        
        # 生成报告
        report = {
            "task_summary": {
                "task_type": "final_disk_creation",
                "start_num": start_num,
                "end_num": end_num,
                "total_disks": total_disks,
                "disk_size_gb": 10,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": success_count/total_disks*100,
                "total_capacity_gb": success_count * 10,
                "environment": self.env_creator.connection_info['name']
            },
            "results": results
        }
        
        # 保存报告
        report_file = f"final_disk_creation_report_{int(start_time)}.json"
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📄 详细报告已保存: {report_file}")
        
        return report

def main():
    """命令行界面"""
    print("🔥 最终磁盘创建器")
    print("从batch-243到batch-1000创建剩余的758个10GB磁盘")
    print("=" * 60)
    
    # 创建最终磁盘创建器实例
    creator = FinalDiskCreator()
    
    # 从batch-243开始创建到batch-1000
    result = creator.create_final_batch(
        start_num=243,
        end_num=1000
    )
    
    total_success = result["task_summary"]["success_count"]
    total_disks = result["task_summary"]["total_disks"]
    
    if total_success > 0:
        print(f"\n🎉 任务成功完成! 成功创建了 {total_success}/{total_disks} 个磁盘")
    else:
        print("\n❌ 任务执行失败!")

if __name__ == "__main__":
    main()