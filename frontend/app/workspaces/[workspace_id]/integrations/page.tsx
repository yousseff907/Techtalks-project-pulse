"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { useMutation, useQuery } from "@tanstack/react-query";

import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";



/*
|--------------------------------------------------------------------------
| Validation
|--------------------------------------------------------------------------
*/


const jiraSchema = z.object({

  base_url: z
    .string()
    .trim()
    .url("Invalid Jira URL format"),


  admin_email: z
    .string()
    .trim()
    .email("Invalid email format"),


  api_key: z
    .string()
    .trim()
    .min(1, "API key is required"),

});



const notionSchema = z.object({

  api_key: z
    .string()
    .trim()
    .min(1, "API key is required"),

});



type JiraFormValues =
  z.infer<typeof jiraSchema>;


type NotionFormValues =
  z.infer<typeof notionSchema>;



type Workspace = {

  role:
    | "owner"
    | "admin"
    | "member";


  jira_connected_at:
    string | null;


  notion_connected_at:
    string | null;

};




export default function IntegrationsPage() {


  const { workspace_id } = useParams();



  const [workspaceState, setWorkspaceState]
    = useState<Workspace | null>(null);



  const [jiraError, setJiraError]
    = useState("");



  const [notionError, setNotionError]
    = useState("");




  /*
  |--------------------------------------------------------------------------
  | Workspace Query
  |
  | Temporary mock
  |
  | Replace with:
  |
  | GET /workspaces/{workspace_id}
  |
  |--------------------------------------------------------------------------
  */


  const {
    data: workspace,
    isLoading,

  } = useQuery({

    queryKey:[
      "workspace",
      workspace_id,
    ],


    queryFn: async():Promise<Workspace> => {


      return {

        role:"owner",

        jira_connected_at:null,

        notion_connected_at:null,

      };



      /*
      REAL BACKEND:

      return api.get(
        `/workspaces/${workspace_id}`
      );

      */


    },


  });




  useEffect(()=>{

    if(workspace){

      setWorkspaceState(workspace);

    }

  },[workspace]);





  /*
  |--------------------------------------------------------------------------
  | Forms
  |--------------------------------------------------------------------------
  */


  const jiraForm =
    useForm<JiraFormValues>({

      resolver:
        zodResolver(jiraSchema),


      defaultValues:{

        base_url:"",

        admin_email:"",

        api_key:"",

      },

    });




  const notionForm =
    useForm<NotionFormValues>({

      resolver:
        zodResolver(notionSchema),


      defaultValues:{

        api_key:"",

      },

    });


  /*
  |--------------------------------------------------------------------------
  | Jira Mutation
  |--------------------------------------------------------------------------
  */


  const jiraMutation =
    useMutation({

      mutationFn:
        async(values:JiraFormValues)=>{


          /*
          ==============================================
          MOCK IMPLEMENTATION
          ==============================================
          */


          await new Promise(
            (resolve)=>
              setTimeout(resolve,800)
          );


          console.log(
            "Mock Jira save:",
            values
          );



          /*
          ==============================================
          REAL BACKEND IMPLEMENTATION

          import api from "@/lib/api";


          return api.patch(
            `/workspaces/${workspace_id}/integrations/jira`,
            values
          );


          ==============================================
          */


        },



      onSuccess:()=>{


        setJiraError("");



        setWorkspaceState(
          (previous)=>({

            ...previous!,

            jira_connected_at:
              new Date()
              .toISOString(),

          })
        );


      },



      onError:(error:any)=>{


        setJiraError(

          error?.response?.data?.detail
          ??
          "Invalid Jira credentials"

        );


      },


    });





  /*
  |--------------------------------------------------------------------------
  | Notion Mutation
  |--------------------------------------------------------------------------
  */


  const notionMutation =
    useMutation({

      mutationFn:
        async(values:NotionFormValues)=>{


          /*
          ==============================================
          MOCK IMPLEMENTATION
          ==============================================
          */


          await new Promise(
            (resolve)=>
              setTimeout(resolve,800)
          );


          console.log(
            "Mock Notion save:",
            values
          );



          /*
          ==============================================
          REAL BACKEND IMPLEMENTATION

          import api from "@/lib/api";


          return api.patch(
            `/workspaces/${workspace_id}/integrations/notion`,
            values
          );


          ==============================================
          */


        },



      onSuccess:()=>{


        setNotionError("");



        setWorkspaceState(
          (previous)=>({

            ...previous!,

            notion_connected_at:
              new Date()
              .toISOString(),

          })
        );


      },



      onError:(error:any)=>{


        setNotionError(

          error?.response?.data?.detail
          ??
          "Invalid Notion credentials"

        );


      },


    });





  if(isLoading || !workspaceState){

    return (

      <div className="p-10">

        Loading...

      </div>

    );

  }




  const readOnly =
    workspaceState.role !== "owner"
    &&
    workspaceState.role !== "admin";

return (

<div className="
max-w-4xl
mx-auto
py-10
space-y-8
">


<h1 className="
text-3xl
font-bold
">
Workspace Integrations
</h1>




{
readOnly && (

<div className="
rounded
border
border-red-300
bg-red-50
p-4
text-red-600
">

You don't have permission to edit integrations.

</div>

)

}




{/* =========================
        Jira
========================= */}


<Card>

<CardHeader>

<CardTitle>
Jira
</CardTitle>

</CardHeader>



<CardContent className="space-y-5">


<Status

connected={
!!workspaceState.jira_connected_at
}

date={
workspaceState.jira_connected_at
}

/>



<form

className="space-y-4"


onSubmit={

jiraForm.handleSubmit(

          (values: JiraFormValues) => {

            setJiraError("");

            jiraMutation.mutate(values);

          }

)

}

>



<div className="space-y-2">


<Label>
Base URL
</Label>


<Input

className="
border
border-input
"


placeholder="
https://company.atlassian.net
"


disabled={readOnly}


{...

jiraForm.register(
"base_url"
)

}


/>



{
jiraForm.formState.errors.base_url && (

<p className="
text-sm
text-red-500
">

{
jiraForm.formState.errors
.base_url
.message
}

</p>

)

}


</div>






<div className="space-y-2">


<Label>
Admin Email
</Label>


<Input

className="
border
border-input
"


placeholder="
admin@example.com
"


disabled={readOnly}


{...

jiraForm.register(
"admin_email"
)

}


/>



{
jiraForm.formState.errors.admin_email && (

<p className="
text-sm
text-red-500
">

{
jiraForm.formState.errors
.admin_email
.message
}

</p>

)

}


</div>






<div className="space-y-2">


<Label>
API Key
</Label>


<Input

type="password"


className="
border
border-input
"


placeholder="
Enter Jira API token
"


disabled={readOnly}


{...

jiraForm.register(
"api_key"
)

}


/>



{
jiraForm.formState.errors.api_key && (

<p className="
text-sm
text-red-500
">

{
jiraForm.formState.errors
.api_key
.message
}

</p>

)

}


</div>





{
jiraError && (

<div className="
text-red-600
">

{jiraError}

</div>

)

}




{
!readOnly && (

<Button

type="submit"


disabled={
jiraMutation.isPending
}

>

{
jiraMutation.isPending
?
"Saving..."
:
"Save Jira"
}


</Button>

)

}



</form>



</CardContent>


</Card>






{/* =========================
        Notion
========================= */}


<Card>


<CardHeader>

<CardTitle>
Notion
</CardTitle>

</CardHeader>



<CardContent className="space-y-5">


<Status

connected={
!!workspaceState.notion_connected_at
}


date={
workspaceState.notion_connected_at
}

/>





<form

className="space-y-4"


onSubmit={

notionForm.handleSubmit(

(values: NotionFormValues)=>{

setNotionError("");

notionMutation.mutate(values);

}

)

}

>




<div className="space-y-2">


<Label>
API Key
</Label>



<Input


type="password"


className="
border
border-input
"


placeholder="
Enter Notion integration token
"


disabled={readOnly}



{...

notionForm.register(
"api_key"
)

}


/>



{
notionForm.formState.errors.api_key && (

<p className="
text-sm
text-red-500
">

{
notionForm.formState.errors
.api_key
.message
}

</p>

)

}



</div>





{
notionError && (

<div className="
text-red-600
">

{notionError}

</div>

)

}





{
!readOnly && (

<Button

type="submit"


disabled={
notionMutation.isPending
}

>

{
notionMutation.isPending
?
"Saving..."
:
"Save Notion"
}


</Button>

)

}



</form>



</CardContent>


</Card>



</div>


);

}





function Status({

connected,

date,

}:{

connected:boolean;

date:string|null;

}){


return (

<div>


<p className="font-medium">

Status

</p>




<p

className={
connected
?
"text-green-600"
:
"text-gray-500"
}

>

{

connected
?
"Connected"
:
"Not Connected"

}


</p>





{

date && (

<p className="
text-sm
text-muted-foreground
">

Connected at:

{" "}

{

new Date(date)
.toLocaleString()

}


</p>

)

}



</div>


);


}