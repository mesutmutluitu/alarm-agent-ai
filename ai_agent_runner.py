from command_planner import generate_command_list
from deep_ssh_executor import run_all_commands
from result_analyzer import analyze_results

def main():
    ip = input("Sunucu IP adresini girin: ")
    alarm = input("Alarm mesajını girin: ")

    print("\n🔍 [1] Komut planlanıyor...")
    commands = generate_command_list(alarm)
    print("🔧 Çalıştırılacak komutlar:")
    for c in commands:
        print(f" - {c}")

    print("\n🚀 [2] Komutlar çalıştırılıyor...")
    results = run_all_commands(ip, commands)

    print("\n🧠 [3] AI analizi yapılıyor...")
    final_analysis = analyze_results(alarm, results)

    print("\n📋 [SONUÇ]:")
    print(final_analysis)

if __name__ == "__main__":
    main()