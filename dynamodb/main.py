"""
Sample code demonstrating many of the common tasks for DynamoDB, including:
- Creating a table (and waiting for the creation to complete)
- Loading data
- Updating an item
- Querying for data using a typical query by key expression
- Querying (scanning) the table and using pagination
- Querying using PartiQL for a more SQL like query style
"""
import boto3, decimal
import json
from boto3.dynamodb.types import TypeDeserializer

def main():
    """
    Perform all of the tasks outlined above
    """
    # Initialize variables, including the DDB client and resource references
    ddbClient = boto3.client('dynamodb')
    ddbResource = boto3.resource('dynamodb')
    jsonFileName = "notes.json"
    tableName = "Notes"

    # Create a table if it doesn't already exist
    if not checkTableExists(ddbClient, tableName):
        print("Table does not exist - creating it")
        creationResponse = createTable(ddbClient, tableName)
        print('Table Status: ' + creationResponse['TableDescription']['TableStatus'])
        print('\nWaiting for the table to be available...\n')
        waitForTableCreate(ddbClient, tableName)

    tableOutput = getTableInfo(ddbClient, tableName)
    print('Table Status: ' + tableOutput['Table']['TableStatus'])

    # Now put some data
    print("\n Loading \"" + tableName +
        "\" table with data from file \"" + jsonFileName + "\"\n\n")
    f = open(jsonFileName)
    notes = json.load(f)
    for n in notes:
        putNote(ddbResource, tableName, n)
    f.close()

    # Update an entry
    print("\nUpdating a note\n")
    updateResponse = updateNote(ddbClient, tableName, "student", 5 )
    print(updateResponse)

    # Query data
    queryResults = queryNotes(ddbClient, tableName, "student" )
    printNotes(queryResults["Items"])
    
    # Pagination
    print("\nScanning using pagination\n")
    queryPagination(ddbClient, tableName, 3)

    # Query using Partiql
    print("\nQuery using PartiQl")
    queryResults = partiqlQuery(ddbClient, tableName, "student", 5)
    printNotes(queryResults["Items"])


def createTable(client, tableName):
    """
    Create a DynamoDB table with the specified name in the default region 

    :param s3Client: string
    :param tableName: string
    :return: response Representing the result of the table creation
    """
    response = client.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': "UserId",
                'AttributeType': 'S',
            },
            {
                'AttributeName': "NoteId",
                'AttributeType': 'N',
            },
        ],
        KeySchema=[
            {
                'AttributeName': "UserId",
                'KeyType': 'HASH',
            },
            {
                'AttributeName': "NoteId",
                'KeyType': 'RANGE',
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5,
        },
        TableName=tableName
    )
    return response

def waitForTableCreate(client, tableName):
    waiter = client.get_waiter('table_exists')
    waiter.wait(TableName=tableName)

def checkTableExists(client, tableName): 
    try:
        response = client.describe_table(TableName=tableName)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False

def getTableInfo(client, tableName):
    response = client.describe_table(
        TableName=tableName
    )

    return response

def putNote(ddbResource, tableName, note):
    table = ddbResource.Table(tableName)
    table.put_item(
        Item={
            'UserId': note["UserId"],
            'NoteId': int(note["NoteId"]),
            'Note': note["Note"]
        }
    )

def updateNote(client, tableName, userId, noteId ):
    response = client.update_item(
        TableName=tableName,
        Key={
            'UserId': {'S': userId},
            'NoteId': {'N': str(noteId)}
        },
        ReturnValues='ALL_NEW',
        UpdateExpression='SET Is_Incomplete = :incomplete',
        ExpressionAttributeValues={
            ':incomplete': {'S': 'Yes'}
        }
    )
    return response['Attributes']


def queryNotes(client, tableName, qUserId):
    response = client.query(
        TableName=tableName,
        KeyConditionExpression='UserId = :userId',
        ExpressionAttributeValues={
            ':userId': {"S": qUserId}
        },
        ProjectionExpression="NoteId, Note"
    )
    return response

def queryPagination(client, tableName, pageSize):
    paginator = client.get_paginator('scan')
    page_iterator = paginator.paginate(
        TableName = tableName,
        PaginationConfig={
            'PageSize': pageSize
        })
    page_number = 0
    for page in page_iterator:
        if page["Count"] > 0:
            page_number += 1
            print("Starting page " + str(page_number))
            printNotes(page['Items'])
            print("End of page " + str(page_number) + "\n")

def partiqlQuery(client, tableName, userId, noteId):
    response = client.execute_statement(
        Statement="SELECT * FROM " + tableName + " WHERE UserId = ? AND NoteId = ?",
        Parameters=[
            {"S": userId},
            {"N": str(noteId)}
        ]
    )
    return response


## Utility methods
def printNotes(notes):
    if isinstance(notes, list):
        for note in notes:
            print(
                json.dumps(
                    {key: TypeDeserializer().deserialize(value) for key, value in note.items()},
                    cls=DecimalEncoder
                )
            )

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        if isinstance(o, set):  # <---resolving sets as lists
            return list(o)
        return super(DecimalEncoder, self).default(o)

main()