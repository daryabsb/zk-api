using System;

namespace ZKBiometricWrapper
{
    [Serializable]
    public class AppSettings
    {
        public bool UseAutoPort { get; set; } = true;
        public int ManualPort { get; set; } = 5000;
        public bool AutoStart { get; set; } = false;

        // Add more settings later if needed
        // public string DefaultIp { get; set; }
        // public int TimeoutSeconds { get; set; } = 30;
    }
}