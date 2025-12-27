using System;
using System.IO;
using System.Net;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ZKBiometricWrapper
{
    public class AppSettings
    {
        public bool UseAutoPort { get; set; } = true;
        public int ManualPort { get; set; } = 5000;
        public bool AutoStart { get; set; } = false;
    }

    static class Program
    {
        private static NotifyIcon? notifyIcon;
        private static ContextMenuStrip? contextMenu;
        private static ToolStripMenuItem? statusItem;
        private static HttpListener? listener;
        private static bool isRunning = false;
        private static readonly ZKBiometricDLL.ZKBiometricAPI api = new();

        private static AppSettings CurrentSettings = new();

        private static ToolStripMenuItem? startItem;
        private static ToolStripMenuItem? stopItem;

        // Settings file in %LocalAppData%\ZKBiometricWrapper\settings.json
        private static readonly string SettingsFilePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "ZKBiometricWrapper",
            "settings.json"
        );

        public const int MIN_PORT = 5000;
        public const int MAX_PORT = 5030;

        [STAThread]
        static void Main()
        {
            ApplicationConfiguration.Initialize();
            LoadSettings();
            RunTrayApplication();
        }

        private static void EnsureSettingsDirectory()
        {
            var directory = Path.GetDirectoryName(SettingsFilePath);
            if (!Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory!);
            }
        }

        private static void LoadSettings()
        {
            EnsureSettingsDirectory();

            if (!File.Exists(SettingsFilePath))
            {
                SaveSettings(new AppSettings()); // Create default
                return;
            }

            try
            {
                var json = File.ReadAllText(SettingsFilePath);
                CurrentSettings = JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to load settings: {ex.Message}\nUsing defaults.", "Settings Error");
                CurrentSettings = new AppSettings();
            }
        }

        private static void SaveSettings(AppSettings settings)
        {
            try
            {
                EnsureSettingsDirectory();
                var json = JsonSerializer.Serialize(settings, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(SettingsFilePath, json);
                CurrentSettings = settings;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to save settings: {ex.Message}", "Save Error");
            }
        }

        private static void RunTrayApplication()
        {
            notifyIcon = new NotifyIcon
            {
                Icon = System.Drawing.SystemIcons.Application,
                Text = "ZK Biometric Wrapper",
                Visible = true
            };

            contextMenu = new ContextMenuStrip();

            statusItem = new ToolStripMenuItem("Status: Stopped") { Enabled = false };
            // statusItem.Enabled = false;
            contextMenu.Items.Add(statusItem);

            contextMenu.Items.Add(new ToolStripSeparator());

            var configItem = new ToolStripMenuItem("Configure...");
            configItem.Click += ConfigItem_Click;
            contextMenu.Items.Add(configItem);

            var startItem = new ToolStripMenuItem("Start Server");
            startItem.Click += async (s, e) => await StartServerAsync();
            contextMenu.Items.Add(startItem);

            var stopItem = new ToolStripMenuItem("Stop Server");
            stopItem.Click += (s, e) => StopServer();
            stopItem.Enabled = false; // initially disabled
            contextMenu.Items.Add(stopItem);

            var restartItem = new ToolStripMenuItem("Restart Server");
            restartItem.Click += async (s, e) => { StopServer(); await StartServerAsync(); };
            contextMenu.Items.Add(restartItem);

            contextMenu.Items.Add(new ToolStripSeparator());

            var exitItem = new ToolStripMenuItem("Exit");
            exitItem.Click += (s, e) =>
            {
                StopServer();
                notifyIcon.Visible = false;
                Application.Exit();
            };
            contextMenu.Items.Add(exitItem);

            notifyIcon.ContextMenuStrip = contextMenu;

            UpdateMenuState(); // initial state

            // if (CurrentSettings.AutoStart)
            // {
            _ = StartServerAsync();
            // }

            Application.Run();
        }

        private static async Task StartServerAsync()
        {
            if (isRunning) return;

            int port = GetConfiguredPort();

            if (port == 0) // Auto mode
            {
                port = FindFreePortInRange();
                if (port == 0)
                {
                    MessageBox.Show($"No free port found in range {MIN_PORT}-{MAX_PORT}!", "Error");
                    return;
                }
            }

            try
            {
                listener = new HttpListener();
                listener.Prefixes.Clear();
                listener.Prefixes.Add($"http://localhost:{port}/");
                listener.Start();

                isRunning = true;
                UpdateMenuState();
                UpdateStatus($"Listening on http://localhost:{port}/");

                _ = Task.Run(async () =>
                {
                    try
                    {
                        while (isRunning)
                        {
                            var context = await listener.GetContextAsync();
                            _ = Task.Run(() => ProcessRequest(context));
                        }
                    }
                    catch { /* expected when stopping */ }
                });
            }
            catch (Exception ex)
            {
                UpdateStatus("Error");
                MessageBox.Show($"Server start failed: {ex.Message}", "Error");
                isRunning = false;
            }
        }

        private static void StopServer()
        {
            if (!isRunning) return;

            try
            {
                isRunning = false;
                listener?.Stop();
                listener?.Close();
                listener = null;
                UpdateMenuState();
                UpdateStatus("Stopped");
            }
            catch { }
        }

        // The state update method (must exist)
        private static void UpdateMenuState()
        {
            // Console.WriteLine($"UpdateMenuState called - isRunning: {isRunning}");
            Log($"UpdateMenuState called - isRunning: {isRunning}, StartEnabled: {startItem?.Enabled}, StopEnabled: {stopItem?.Enabled}");
            if (startItem != null)
                startItem.Enabled = !isRunning;

            if (stopItem != null)
                stopItem.Enabled = isRunning;

            if (statusItem != null)
                statusItem.Text = isRunning ? "Status: Running" : "Status: Stopped";
        }

        private static readonly string LogPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "ZKBiometricWrapper",
            "debug.log"
        );

        private static void Log(string message)
        {
            try
            {
                string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
                string line = $"[{timestamp}] {message}{Environment.NewLine}";
                
                Directory.CreateDirectory(Path.GetDirectoryName(LogPath)!);
                File.AppendAllText(LogPath, line);
            }
            catch { /* silent fail - don't crash app on logging error */ }
        }

        private static int GetConfiguredPort()
        {
            return CurrentSettings.UseAutoPort ? 0 : CurrentSettings.ManualPort;
        }

        private static int FindFreePortInRange()
        {
            for (int p = MIN_PORT; p <= MAX_PORT; p++)
            {
                try
                {
                    using var testListener = new HttpListener();
                    testListener.Prefixes.Add($"http://localhost:{p}/");
                    testListener.Start();
                    return p;
                }
                catch { }
            }
            return 0;
        }

        private static void UpdateStatus(string message)
        {
            if (statusItem != null)
                statusItem.Text = $"Status: {message}";

            if (notifyIcon != null)
                notifyIcon.Text = $"ZK Wrapper - {message}";
        }

        private static void ConfigItem_Click(object? sender, EventArgs e)
        {
            using var form = new PortConfigForm(CurrentSettings);
            if (form.ShowDialog() == DialogResult.OK)
            {
                SaveSettings(form.Settings);

                if (isRunning)
                {
                    StopServer();
                    _ = StartServerAsync();
                }
            }
        }

        static async Task ProcessRequest(HttpListenerContext context)
        {
            try
            {
                var request = context.Request;
                var response = context.Response;

                response.ContentType = "application/json";

                string path = request.Url.AbsolutePath.ToLowerInvariant();
                string method = request.HttpMethod.ToUpperInvariant();

                string result;

                if (method == "GET" && path == "/test-connection")
                    result = HandleTestConnection(request);
                else if (method == "GET" && path == "/employees")
                    result = HandleGetEmployees(request);
                else if (method == "GET" && path == "/attendance")
                    result = HandleGetAttendance(request);
                else
                {
                    response.StatusCode = 404;
                    result = "{\"success\": false, \"error\": \"Invalid endpoint\"}";
                }

                var buffer = Encoding.UTF8.GetBytes(result);
                response.ContentLength64 = buffer.Length;
                await response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
                response.OutputStream.Close();
            }
            catch { }
        }

        static string HandleTestConnection(HttpListenerRequest request)
        {
            var (success, message) = GetDeviceFromRequest(request, out var device);
            if (!success) return message!;

            string deviceJson = JsonSerializer.Serialize(device);
            return api.TestConnection(deviceJson);
        }

        static string HandleGetEmployees(HttpListenerRequest request)
        {
            var (success, message) = GetDeviceFromRequest(request, out var device);
            if (!success) return message!;

            string deviceJson = JsonSerializer.Serialize(device);
            return api.GetEmployees(deviceJson);
        }

        static string HandleGetAttendance(HttpListenerRequest request)
        {
            string start = request.QueryString["start"] ?? "";
            string end = request.QueryString["end"] ?? "";

            if (string.IsNullOrWhiteSpace(start) || string.IsNullOrWhiteSpace(end))
                return "{\"success\": false, \"error\": \"Missing start or end query parameter\"}";

            var (success, message) = GetDeviceFromRequest(request, out var device);
            if (!success) return message!;

            string deviceJson = JsonSerializer.Serialize(device);
            return api.GetAttendanceRecords(deviceJson, start, end);
        }

        private static (bool success, string? error) GetDeviceFromRequest(HttpListenerRequest request, out object? device)
        {
            device = null;

            string ip = request.QueryString["ip"] ?? "";
            string portStr = request.QueryString["port"] ?? "4370";

            if (!int.TryParse(portStr, out int port))
                port = 4370;

            if (string.IsNullOrWhiteSpace(ip))
            {
                return (false, "{\"success\": false, \"error\": \"Missing ip query parameter\"}");
            }

            device = new
            {
                IpAddress = ip,
                Port = port,
                Name = $"Device-{ip}",
                IsEnabled = true
            };

            return (true, null);
        }

    }

    // Configuration Form
    public class PortConfigForm : Form
    {
        public AppSettings Settings { get; private set; }

        private readonly RadioButton rbManual;
        private readonly RadioButton rbAuto;
        private readonly NumericUpDown numPort;
        private readonly CheckBox autoStartChk;

        public PortConfigForm(AppSettings initialSettings)
        {
            Settings = new AppSettings
            {
                UseAutoPort = initialSettings.UseAutoPort,
                ManualPort = initialSettings.ManualPort,
                AutoStart = initialSettings.AutoStart
            };

            Text = "ZK Wrapper Configuration";
            Size = new System.Drawing.Size(380, 220);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            StartPosition = FormStartPosition.CenterParent;

            var lbl = new Label { Text = "HTTP Server Port:", Left = 20, Top = 20, AutoSize = true };
            Controls.Add(lbl);

            rbManual = new RadioButton
            {
                Text = "Manual port:",
                Location = new System.Drawing.Point(20, 50),
                Checked = !initialSettings.UseAutoPort
            };
            Controls.Add(rbManual);

            numPort = new NumericUpDown
            {
                Location = new System.Drawing.Point(140, 48),
                Minimum = 1024,
                Maximum = 65535,
                Value = initialSettings.ManualPort,
                Width = 100,
                Enabled = rbManual.Checked
            };
            Controls.Add(numPort);

            rbAuto = new RadioButton
            {
                Text = $"Automatic (find free port {Program.MIN_PORT}-{Program.MAX_PORT})",
                Location = new System.Drawing.Point(20, 85),
                Checked = initialSettings.UseAutoPort
            };
            Controls.Add(rbAuto);

            autoStartChk = new CheckBox
            {
                Text = "Start server automatically on launch",
                Location = new System.Drawing.Point(20, 115),
                Checked = initialSettings.AutoStart
            };
            Controls.Add(autoStartChk);

            var btnSave = new Button { Text = "Save", Location = new System.Drawing.Point(120, 150), DialogResult = DialogResult.OK };
            btnSave.Click += (s, e) =>
            {
                Settings.UseAutoPort = rbAuto.Checked;
                Settings.ManualPort = (int)numPort.Value;
                Settings.AutoStart = autoStartChk.Checked;
            };
            Controls.Add(btnSave);

            var btnCancel = new Button { Text = "Cancel", Location = new System.Drawing.Point(220, 150), DialogResult = DialogResult.Cancel };
            Controls.Add(btnCancel);

            rbManual.CheckedChanged += (s, e) => numPort.Enabled = rbManual.Checked;
        }
    }

}