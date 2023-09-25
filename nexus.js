// Copyright (c) 2023, wns and contributors
// For license information, please see license.txt

// async function transcribeRow(row, frm) {
//     const prompt = frm.doc.preengineered_prompt;

//     frappe.call({
//         method: 'nextgen.nextgen.doctype.nexus.nexus.transcribe', // API method to call
//         args: {
//             file_path: row.assessment_label,
//             prompt: prompt,
//         },
//         callback: function(response) {

//             try {
//                 console.log("In respose")
//                 console.log(response)
//                 const transcription = response.message;

//                 row.score = transcription;

//                 frm.refresh_field('output');

//                 frappe.call({
//                     method: "nextgen.nextgen.doctype.nexus.nexus.send_to_ai",
//                     args: {
//                         prompt: prompt,
//                         transcription: transcription
//                     },
//                     callback: function(response) {
//                         console.log("IN CHAT RESPONSE");
//                         console.log(response)

//                         row.result = response.message;
//                         row.status = 'Done'

//                         frm.refresh_field('output');
//                     }
//                 })
//             } catch (error) {
//                 row.status = "Error"
//                 frm.refresh_field('output');
//             }
            
//         }})
// }

frappe.ui.form.on('NEXUS', {
	refresh: function(frm) {
        // Attach the function to the button's click event
        frm.add_custom_button(__('Call Upload API'), function() {
            // Make the API call using frappe.call
            var prompt = frm.doc.preengineered_prompt;
            console.log(frm);
            console.log(prompt)
            console.log(frm.doc.attach)

            const scoreHeadersRegex = /SCORE_HEADERS:\s*\[([\s\S]*?)\]/;
            const match = prompt.match(scoreHeadersRegex);
            let scoreHeadersArray = [];
            if (match) {
            const scoreHeadersText = match[1];
                scoreHeadersArray = scoreHeadersText
                    .split(',')
                    .map(item => item.trim());
                
                scoreHeadersArray = scoreHeadersArray.map((str) => {
                    // Convert the string to lowercase
                    const lowercaseStr = str.toLowerCase();
                  
                    // Replace spaces with underscores
                    const modifiedStr = lowercaseStr.replace(/ /g, '_');
                  
                    return modifiedStr;
                  });

                console.log(scoreHeadersArray);
            } else {
                console.log("SCORE_HEADERS not found in the input string.");
            }

            frappe.call({
                method:  'nextgen.nextgen.doctype.nexus.nexus.get_results',
                args: {
                    docname: frm.docname,
                    prompt: prompt,
                    scores: scoreHeadersArray,
                },
                callback: function(response) {
                    console.log("DONE");
                }
            })

            // frappe.call({
            //     method: 'nextgen.nextgen.doctype.nexus.nexus.get_all_attachment_paths',
            //     args: {
            //         docname: frm.docname
            //     },
            //     callback: function(response) {
            //         const files = response.message.files;
            //         console.log(files);
                    
            //         let rows = [];
            //         for (const file of files) {
            //             rows.push(frm.add_child('output', {assessment_label: file, status: 'Not Done'}));
            //         }

            //         for (const row of rows) {
            //             transcribeRow(row, frm);
            //         }

            //         console.log("ROW::::", rows);
            //         frm.refresh_field('output');
            //     }
            // })
            
            // Check if the file input element exists
            // var fileInput = frm.doc.attach
            // if (fileInput) {
            //     // var selectedFile = fileInput.files[0];
            //     frappe.msgprint("Attached File");
            //     // Perform the API call
            //     frappe.call({
            //         method: 'nextgen.nextgen.doctype.nexus.nexus.transcribe', // API method to call
            //         args: {
            //             file_path: fileInput,
            //             prompt: prompt,
            //         },
            //         callback: function(response) {
            //             // Handle the API response here
            //             console.log("In respose")
            //             console.log(response)
            //             const transcription = response.message.transcription;
            //             frm.doc.transcript = transcription;

            //             frm.add_child('output', response.message.output);

            //             frm.refresh_field('transcript');
            //             frm.refresh_field('output');
            //             console.log(frm)

            //             // frappe.call({
            //             //     method: "nextgen.nextgen.doctype.nexus.nexus.send_to_ai",
            //             //     args: {
            //             //         prompt: prompt,
            //             //         transcription: transcription
            //             //     },
            //             //     callback: function(response) {
            //             //         console.log("IN CHAT RESPONSE");
            //             //         console.log(response)

            //             //         frm.doc.result = response.message;
            //             //         frm.refresh_field('result');

            //             //         console.log("RESULT IS:::::::", frm.doc.result);
            //             //         frm.dirty();
            //             //         frm.save();
            //             //     }
            //             // })
            //         }
            //     });
            // } else {
            //     frappe.msgprint("File input element not found.");
            // }
        });
    }
});

