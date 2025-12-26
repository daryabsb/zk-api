using System;
using System.Net;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ZKBiometricWrapper
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            ApplicationConfiguration.Initialize();
            RunTrayApplication();
        }

        private static void RunTrayApplication()
        {
            var notifyIcon = new NotifyIcon
            {
                Icon = System.Drawing.SystemIcons.Application,
                Text = "ZK Biometric Wrapper",
                Visible = true
            };

            var contextMenu = new ContextMenuStrip();

            var statusItem = new ToolStripMenuItem("Status: Starting...");
            statusItem.Enabled = false;
            contextMenu.Items.Add(statusItem);

            contextMenu.Items.Add(new ToolStripSeparator());

            var exitItem = new ToolStripMenuItem("Exit");
            exitItem.Click += (s, e) =>
            {
                notifyIcon.Visible = false;
                Application.Exit();
            };
            contextMenu.Items.Add(exitItem);

            notifyIcon.ContextMenuStrip = contextMenu;

            var api = new ZKBiometricDLL.ZKBiometricAPI();
            var listener = new HttpListener();
            listener.Prefixes.Add("http://localhost:5000/");

            Task.Run(async () =>
            {
                try
                {
                    listener.Start();

                    statusItem.Text = "Status: Listening on http://localhost:5000/";

                    while (true)
                    {
                        var context = await listener.GetContextAsync();
                        _ = Task.Run(() => ProcessRequest(context, api));
                    }
                }
                catch (Exception ex)
                {
                    statusItem.Text = "Status: Error";
                    MessageBox.Show($"Error starting ZK Biometric Wrapper: {ex.Message}", "ZK Wrapper", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            });

            Application.Run();
        }

        static async Task ProcessRequest(HttpListenerContext context, ZKBiometricDLL.ZKBiometricAPI api)
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
                {
                    result = HandleTestConnection(request, api);
                }
                else if (method == "GET" && path == "/employees")
                {
                    result = HandleGetEmployees(request, api);
                }
                else if (method == "GET" && path == "/attendance")
                {
                    result = HandleGetAttendance(request, api);
                }
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
            catch (Exception ex)
            {
                // Swallow per-request exceptions to keep server running
            }
        }

        static string HandleTestConnection(HttpListenerRequest request, ZKBiometricDLL.ZKBiometricAPI api)
        {
            string ip = request.QueryString["ip"] ?? string.Empty;
            string portValue = request.QueryString["port"] ?? "4370";
            int port = int.TryParse(portValue, out var parsedPort) ? parsedPort : 4370;

            if (string.IsNullOrWhiteSpace(ip))
            {
                return "{\"success\": false, \"error\": \"Missing ip query parameter\"}";
            }

            var device = new
            {
                IpAddress = ip,
                Port = port,
                Name = $"Device-{ip}",
                IsEnabled = true
            };

            string deviceJson = JsonSerializer.Serialize(device);
            return api.TestConnection(deviceJson);
        }

        static string HandleGetEmployees(HttpListenerRequest request, ZKBiometricDLL.ZKBiometricAPI api)
        {
            string ip = request.QueryString["ip"] ?? string.Empty;
            string portValue = request.QueryString["port"] ?? "4370";
            int port = int.TryParse(portValue, out var parsedPort) ? parsedPort : 4370;

            if (string.IsNullOrWhiteSpace(ip))
            {
                return "{\"success\": false, \"error\": \"Missing ip query parameter\"}";
            }

            var device = new
            {
                IpAddress = ip,
                Port = port,
                Name = $"Device-{ip}",
                IsEnabled = true
            };

            string deviceJson = JsonSerializer.Serialize(device);
            return api.GetEmployees(deviceJson);
        }

        static string HandleGetAttendance(HttpListenerRequest request, ZKBiometricDLL.ZKBiometricAPI api)
        {
            string ip = request.QueryString["ip"] ?? string.Empty;
            string portValue = request.QueryString["port"] ?? "4370";
            int port = int.TryParse(portValue, out var parsedPort) ? parsedPort : 4370;
            string start = request.QueryString["start"];
            string end = request.QueryString["end"];

            if (string.IsNullOrWhiteSpace(ip))
            {
                return "{\"success\": false, \"error\": \"Missing ip query parameter\"}";
            }

            if (string.IsNullOrWhiteSpace(start) || string.IsNullOrWhiteSpace(end))
            {
                return "{\"success\": false, \"error\": \"Missing start or end query parameter\"}";
            }

            var device = new
            {
                IpAddress = ip,
                Port = port,
                Name = $"Device-{ip}",
                IsEnabled = true
            };

            string deviceJson = JsonSerializer.Serialize(device);
            return api.GetAttendanceRecords(deviceJson, start, end);
        }
    }
}
