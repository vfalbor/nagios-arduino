#include <GSM.h>

// PIN Number
#define PINNUMBER ""

// initialize the library instance
GSM gsmAccess; // include a 'true' parameter for debug enabled
GSMVoiceCall vcs;

String remoteNumber = "";  // the number you will call
char charbuffer[20];

void setup()
{

  // initialize serial communications
  Serial.begin(9600); 

  Serial.println("Make Voice Call");

  // connection state
  boolean notConnected = true;

  // Start GSM shield
  // If your SIM has PIN, pass it as a parameter of begin() in quotes
  while(notConnected)
  {
    if(gsmAccess.begin(PINNUMBER)==GSM_READY)
      notConnected = false;
    else
    {
      Serial.println("Not connected");
      delay(1000);
    }
  }

  Serial.println("GSM initialized.");
  Serial.println("Enter phone number to call.");

}

void loop()
{

  // add any incoming characters to the String:
  while (Serial.available() > 0)
  {
    char inChar = Serial.read();
    // if it's a newline, that means you should make the call:
    if (inChar == '\n')
    {
      // make sure the phone number is not too long:
      if (remoteNumber.length() < 20)
      {
        // show the number you're calling:
        Serial.print("Calling to : ");
        Serial.println(remoteNumber);
        Serial.println();

        // Call the remote number
        remoteNumber.toCharArray(charbuffer, 20);


        // Check if the receiving end has picked up the call
        if(vcs.voiceCall(charbuffer))
        {
          Serial.println("Call Established. Enter line to end");
          // Wait for some input from the line
          while(Serial.read()!='\n' && (vcs.getvoiceCallStatus()==TALKING));          
          // And hang up
          vcs.hangCall();
        }
        Serial.println("Call Finished");
        remoteNumber="";
        Serial.println("Enter phone number to call.");
      } 
      else
      {
        Serial.println("That's too long for a phone number. I'm forgetting it"); 
        remoteNumber = "";
      }
    } 
    else
    {
      // add the latest character to the message to send:
      if(inChar!='\r')
        remoteNumber += inChar;
    }
  } 
}

