// updates a games texture to images recieved over a tcp stream
// add to gameobject to change that object's material's texture

using UnityEngine;
using System.Collections;
using UnityEngine.UI;
using System.Net.Sockets;
using System.Net;
using System.IO;
using System;
using System.Text;

// tcp client for streaming png images
// code from client.cs on https://stackoverflow.com/questions/42717713/unity-live-video-streaming

public class TCPPNGMaterialStream : MonoBehaviour
{
   //  public RawImage image;
    public bool enableLog = false;

    const int port = 5001;
    public string IP = "localhost"; // "192.168.1.165"; // TODO
    TcpClient client;

    Texture2D tex;

    private bool stop = false;

    //This must be the-same with SEND_COUNT on the server
    const int SEND_RECEIVE_COUNT = 8;  // unsigned long long is 8 bytes

    // Use this for initialization
    void Start()
    {
        Application.runInBackground = true;

        tex = new Texture2D(0, 0);
        client = new TcpClient();

        //Connect to server from another Thread
        Loom.RunAsync(() =>
        {
            LOGWARNING("Connecting to server...");
            // if on desktop
            client.Connect(IPAddress.Loopback, port);

            // if using the IPAD
            //client.Connect(IPAddress.Parse(IP), port);
            LOGWARNING("Connected!");

            imageReceiver();
        });
    }


    void imageReceiver()
    {
        //While loop in another Thread is fine so we don't block main Unity Thread
        Loom.RunAsync(() =>
        {
            while (!stop)
            {
                //Read Image Count
                int imageSize = readImageByteSize(SEND_RECEIVE_COUNT);
                LOGWARNING("Received Image byte Length: " + imageSize);

                //Read Image Bytes and Display it
                readFrameByteArray(imageSize);
            }
        });
    }


    //Converts the data size to byte array and put result to the fullBytes array
    void byteLengthToFrameByteArray(int byteLength, byte[] fullBytes)
    {
        //Clear old data
        Array.Clear(fullBytes, 0, fullBytes.Length);
        //Convert int to bytes
        byte[] bytesToSendCount = BitConverter.GetBytes(byteLength);
        //Copy result to fullBytes
        bytesToSendCount.CopyTo(fullBytes, 0);
    }

    //Converts the byte array to the data size and returns the result
    int frameByteArrayToByteLength(byte[] frameBytesLength)
    {
        int byteLength = BitConverter.ToInt32(frameBytesLength, 0);
        return byteLength;
    }


    /////////////////////////////////////////////////////Read Image SIZE from Server///////////////////////////////////////////////////
    private int readImageByteSize(int size)
    {
        bool disconnected = false;

        NetworkStream serverStream = client.GetStream();
        byte[] imageBytesCount = new byte[size];
        var total = 0;
        do
        {
            var read = serverStream.Read(imageBytesCount, total, size - total);
            // Debug.LogFormat("Client recieved {0} bytes", total);
            if (read == 0)
            {
                disconnected = true;
                break;
            }
            total += read;
        } while (total != size);

        int byteLength;

        if (disconnected)
        {
            byteLength = -1;
        }
        else
        {
            byteLength = frameByteArrayToByteLength(imageBytesCount);
        }
        return byteLength;
    }

    /////////////////////////////////////////////////////Read Image Data Byte Array from Server///////////////////////////////////////////////////
    private void readFrameByteArray(int size)
    {
        bool disconnected = false;

        NetworkStream serverStream = client.GetStream();
        byte[] imageBytes = new byte[size];
        var total = 0;
        do
        {
            var read = serverStream.Read(imageBytes, total, size - total);
            //Debug.LogFormat("Client recieved {0} bytes", total);
            if (read == 0)
            {
                disconnected = true;
                break;
            }
            total += read;
        } while (total != size);

        bool readyToReadAgain = false;

        //Display Image
        if (!disconnected)
        {
            //Display Image on the main Thread
            Loom.QueueOnMainThread(() =>
            {
                displayReceivedImage(imageBytes);
                readyToReadAgain = true;
            });
        }

        //Wait until old Image is displayed
        while (!readyToReadAgain)
        {
            System.Threading.Thread.Sleep(1);
        }
    }


    void displayReceivedImage(byte[] imgBytes64)
    {
        //Mat byteMat = new Mat(1, imgBytes.Length, CvType.CV_8UC1);  // TODO edit types
        //Utils.copyToMat<byte>(imgBytes, byteMat);
        //Mat decodedImage = Imgcodecs.imdecode(byteMat, Imgcodecs.CV_LOAD_IMAGE_COLOR); // todo match with encoding on server
        //Imgproc.cvtColor(decodedImage, decodedImage, Imgproc.COLOR_BGR2RGB); 

        // decode base64 strings
        string s = System.Text.Encoding.UTF8.GetString(imgBytes64, 0, imgBytes64.Length);

        byte[] imgBytes = Convert.FromBase64String(s);

        // log experiments
        LOG(System.Text.Encoding.UTF8.GetString(imgBytes, 0, imgBytes.Length)); // should have img logo, if chars show in debugger there's a problem
        tex.LoadImage(imgBytes);
        GetComponent<Renderer>().material.mainTexture = tex;
    }


    void LOG(string messsage)
    {
        if (enableLog)
            Debug.Log(messsage);
    }

    void LOGWARNING(string messsage)
    {
        if (enableLog)
            Debug.LogWarning(messsage);
    }

    void OnApplicationQuit()
    {
        LOGWARNING("OnApplicationQuit");
        stop = true;

        if (client != null)
        {
            client.Close();
        }
    }
}