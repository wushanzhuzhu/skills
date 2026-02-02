#!/usr/bin/env python3
"""
批量磁盘创建脚本 - 在生产环境创建10个10GB磁盘
"""

from env_disk_creator import EnvironmentAwareDiskCreator

def create_batch_disks():
    """批量创建10个10GB磁盘"""
    
    print("🔥 批量磁盘创建任务")
    print("目标环境: 生产环境")
    print("磁盘规格: 10GB x 10个")
    print("=" * 50)
    
    creator = EnvironmentAwareDiskCreator()
    
    # 检查生产环境
    if not creator.check_environment("production"):
        print("❌ 生产环境连接失败，无法执行批量创建")
        return False
    
    results = []
    success_count = 0
    failed_count = 0
    
    for i in range(1, 11):
        print(f"\n📁 创建第 {i}/10 个磁盘...")
        
        try:
            from smart_disk_creator import SmartDiskCreator
            
            # 每次创建新的连接，避免会话冲突
            disk_creator = SmartDiskCreator(
                creator.connection_info['username'],
                creator.connection_info['password'],
                creator.connection_info['url']
            )
            
            success = disk_creator.create_disk_smart(10, "standard")
            
            if success:
                success_count += 1
                print(f"✅ 第 {i} 个磁盘创建成功")
            else:
                failed_count += 1
                print(f"❌ 第 {i} 个磁盘创建失败")
            
            results.append({
                'disk_num': i,
                'success': success
            })
            
            # 添加延迟，避免API频率限制
            if i < 10:  # 最后一个不需要延迟
                print("⏳ 等待2秒后继续...")
                import time
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ 第 {i} 个磁盘创建出错: {e}")
            failed_count += 1
            results.append({
                'disk_num': i,
                'success': False,
                'error': str(e)
            })
    
    # 显示最终结果
    print("\n" + "=" * 60)
    print("📊 批量创建结果汇总")
    print("=" * 60)
    print(f"✅ 成功创建: {success_count}/10")
    print(f"❌ 创建失败: {failed_count}/10")
    print(f"📈 成功率: {success_count/10*100:.1f}%")
    
    print(f"\n🌐 目标环境: {creator.connection_info['name']}")
    print(f"📡 环境地址: {creator.connection_info['url']}")
    print(f"💾 总容量: {success_count * 10}GB")
    
    # 显示详细结果
    if failed_count > 0:
        print(f"\n❌ 失败的磁盘:")
        for result in results:
            if not result['success']:
                error_info = f" - {result.get('error', '未知错误')}" if 'error' in result else ""
                print(f"   磁盘 {result['disk_num']}: 创建失败{error_info}")
    
    print("\n🎉 批量创建任务完成!")
    return success_count == 10

if __name__ == "__main__":
    create_batch_disks()