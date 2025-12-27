5. Optional – Better tray icons (running vs stopped)If you want to visually distinguish running/stopped state:Prepare two small .ico files (16x16 or 32x32):stopped.ico – grey/green icon
   running.ico – green/red icon with play symbol or similar

Add them to project as Embedded resource or Content (Copy if newer)
Load and switch icons:

csharp

private static void UpdateStatus(string message)
{
if (statusItem != null)
statusItem.Text = $"Status: {message}";

    if (notifyIcon != null)
    {
        notifyIcon.Text = $"ZK Wrapper - {message}";

        // Optional: switch icon
        try
        {
            if (isRunning)
            {
                notifyIcon.Icon = new System.Drawing.Icon("running.ico"); // adjust path
            }
            else
            {
                notifyIcon.Icon = new System.Drawing.Icon("stopped.ico");
            }
        }
        catch { /* fallback to default */ }
    }

}

If you don't have custom icons, you can also use system icons:csharp

notifyIcon.Icon = isRunning
? System.Drawing.SystemIcons.Information
: System.Drawing.SystemIcons.Warning;
