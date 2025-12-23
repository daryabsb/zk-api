using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading.Tasks;

namespace ZKBiometricWrapper
{
    class Program
    {
        static async Task Main(string[] args)
        {
            var listener = new HttpListener();
            listener.Prefixes.Add("http://localhost:5000/");
            listener.Start();
            Console.WriteLine("ZK Biometric Wrapper running on http://localhost:5000/");
            
            var api = new ZKBiometricDLL.ZKBiometricAPI();
            
            while (true)
            {
                var context = await listener.GetContextAsync();
                _ = Task.Run(() => ProcessRequest(context, api));
            }
        }
        
        static async Task ProcessRequest(HttpListenerContext context, ZKBiometricDLL.ZKBiometricAPI api)
        {
            try
            {
                var request = context.Request;
                var response = context.Response;
                
                response.ContentType = "application/json";
                
                string result = "{}";
                
                if (request.Url.PathAndQuery == "/test-connection" && request.HttpMethod == "POST")
                {
                    using (var reader = new StreamReader(request.InputStream, request.ContentEncoding))
                    {
                        var deviceJson = await reader.ReadToEndAsync();
                        result = api.TestConnection(deviceJson);
                    }
                }
                else if (request.Url.PathAndQuery == "/get-employees" && request.HttpMethod == "POST")
                {
                    using (var reader = new StreamReader(request.InputStream, request.ContentEncoding))
                    {
                        var deviceJson = await reader.ReadToEndAsync();
                        result = api.GetEmployees(deviceJson);
                    }
                }
                else
                {
                    result = "{\"error\":\"Invalid endpoint\"}";
                    response.StatusCode = 404;
                }
                
                var buffer = Encoding.UTF8.GetBytes(result);
                response.ContentLength64 = buffer.Length;
                await response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
                response.OutputStream.Close();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error processing request: {ex}");
            }
        }
    }
}