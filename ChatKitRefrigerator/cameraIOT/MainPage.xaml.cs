using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices.WindowsRuntime;
using Windows.Foundation;
using Windows.Foundation.Collections;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;


using Windows.Media.Capture;
using Windows.Media.MediaProperties;
using Windows.Storage;
using Windows.Storage.Streams;

using Windows.Devices.Gpio;
using System.Threading.Tasks;
using System.Net.Http;

namespace cameraIOT
{

    /// <summary>
    /// 자체적으로 사용하거나 프레임 내에서 탐색할 수 있는 빈 페이지입니다.
    /// </summary>
    /// 
    public sealed partial class MainPage : Page
    {
        private MediaCapture mediaCapture;
        private StorageFile photoFile;
        private bool isPreviewing;
        private bool isButtonEnabled;

        HttpResponseMessage response;
        MultipartFormDataContent form;
        HttpClient httpClient;
        String nowTime;
        ImageEncodingProperties imageProperties;

        String filename;
        String url = "http://flaskiot.azurewebsites.net";//"localhost:5555";

        private const int BUTTON_PIN = 5;
        private GpioPin buttonPin;

        enum Action
        {
            ENABLE,
            DISABLE
        }

        public MainPage()
        {
            this.InitializeComponent();
            //message reset
            state.Text = "first";
            error.Text = "No error";

            isPreviewing = false;
            takePhotoButton.IsEnabled = false;
            isButtonEnabled = false;
            InitGPIO();
            initButtonAction();

            isButtonEnabled = true;
        }

        private void InitGPIO()
        {
            var gpio = GpioController.GetDefault();
            
            // Show an error if there is no GPIO controller
            if (gpio == null)
            {
                state.Text = "There is no GPIO controller on this device.";
                return;
            }

            buttonPin = gpio.OpenPin(BUTTON_PIN);

            // Check if input pull-up resistors are supported
            if (buttonPin.IsDriveModeSupported(GpioPinDriveMode.InputPullUp))
                buttonPin.SetDriveMode(GpioPinDriveMode.InputPullUp);
            else
                buttonPin.SetDriveMode(GpioPinDriveMode.Input);

            // Set a debounce timeout to filter out switch bounce noise from a button press
            buttonPin.DebounceTimeout = TimeSpan.FromMilliseconds(50);

            //button interrupt by delegate
            buttonPin.ValueChanged += buttonPin_ValueChanged;

            state.Text = "GPIO pins initialized correctly.";
        }

        private void buttonPin_ValueChanged(GpioPin sender, GpioPinValueChangedEventArgs e)
        {
            //debug
            //if (e.Edge == GpioPinEdge.FallingEdge)
            //{
            //    //state.Text = "Button Pressed";
            //    //buttonPin.ValueChanged -= buttonPin_ValueChanged; ;
            //    if (isButtonEnabled == true)
            //    {
            //        isButtonEnabled = false;

            //        takePhoto();

            //        isButtonEnabled = true;

            //    }
            //}

            var task = Dispatcher.RunAsync(Windows.UI.Core.CoreDispatcherPriority.Normal, async () =>
             {
                 if (e.Edge == GpioPinEdge.FallingEdge)
                 {
                     //state.Text = "Button Pressed";
                     if (isButtonEnabled == true)
                     {
                         isButtonEnabled = false;

                         await takePhoto();

                         isButtonEnabled = true;
                     }
                 }
                 //else
                 //{
                 //    state.Text = "Button Released";
                 //}
             });
        }


        private async void initButton_Click(object sender, RoutedEventArgs e)
        {
            await initButtonAction();//
        }

        private async Task initButtonAction()
        {
            try
            {
                initButton.IsEnabled = false;
                if (mediaCapture != null)
                {
                    if (isPreviewing)
                    {
                        await mediaCapture.StopPreviewAsync();
                        previewElement.Source = null;
                        isPreviewing = false;
                    }
                    mediaCapture.Dispose();
                    mediaCapture = null;
                }
                //init
                mediaCapture = new MediaCapture();
                await mediaCapture.InitializeAsync();

                //preview start
                previewElement.Source = mediaCapture;
                await mediaCapture.StartPreviewAsync();
                isPreviewing = true;


                takePhotoButton.IsEnabled = true;
                initButton.IsEnabled = true;

            }
            catch (Exception ex)
            {
                error.Text = ex.Message;
                initButton.IsEnabled = true;
            }
        }

        public async Task<byte[]> ReadFile(StorageFile file)
        {
            byte[] fileBytes = null;
            using (IRandomAccessStreamWithContentType stream = await file.OpenReadAsync())
            {
                fileBytes = new byte[stream.Size];
                using (DataReader reader = new DataReader(stream))
                {
                    await reader.LoadAsync((uint)stream.Size);
                    reader.ReadBytes(fileBytes);
                }
            }

            return fileBytes;
        }

        private async void takePhotoButton_Click(object sender, RoutedEventArgs e)
        {
            

            await takePhoto();

            

            await initButtonAction();

        }

        private async Task takePhoto()
        {
            try
            {
                takePhotoButton.IsEnabled = false;
                initButton.IsEnabled = false;
                isButtonEnabled = false;
                if (isPreviewing)
                {
                                
                    state.Text = "File name";
                    System.Globalization.CultureInfo ci = new System.Globalization.CultureInfo("en-US");
                    nowTime = DateTime.Now.ToString("r", ci);
                    filename = nowTime + ".jpg";
                    filename = filename.Replace(':', ' ');

                    state.Text = "Save File1";
                    photoFile = await KnownFolders.PicturesLibrary.CreateFileAsync(filename, CreationCollisionOption.GenerateUniqueName);
                    state.Text = "Save File2";
                    imageProperties = ImageEncodingProperties.CreateJpeg();
                    state.Text = "Save File3";
                    await mediaCapture.CapturePhotoToStorageFileAsync(imageProperties, photoFile);
                                     

                    state.Text = "Send File";
                    httpClient = new HttpClient();
                    form = new MultipartFormDataContent();
                    //byte[] imagebytearraystring = await ReadFile(imageFile);
                    //form.Add(new ByteArrayContent(imagebytearraystring, 0, imagebytearraystring.Count()), "file", filename);
                    byte[] imagebytearraystring = await ReadFile(photoFile);
                    form.Add(new ByteArrayContent(imagebytearraystring, 0, imagebytearraystring.Count()), "file", filename);

                    state.Text = "Get Response";
                    response = await httpClient.PostAsync(url, form);
                    response.EnsureSuccessStatusCode();
                    httpClient.Dispose();
                    state.Text = response.Content.ReadAsStringAsync().Result;
                }
                
                takePhotoButton.IsEnabled = true;
                initButton.IsEnabled = true;
                isButtonEnabled = true;

            }
            catch (Exception ex)
            {
                state.Text = "Exception";
                error.Text = ex.Message;
                Cleanup();
                await initButtonAction();
            }
        }

        private async void Cleanup()
        {
            if (mediaCapture != null)
            {
                // Cleanup MediaCapture object
                if (isPreviewing)
                {
                    await mediaCapture.StopPreviewAsync();
                    isPreviewing = false;
                }
                
                mediaCapture.Dispose();
                mediaCapture = null;

                takePhotoButton.IsEnabled = false;
            }
        }

    }
}
