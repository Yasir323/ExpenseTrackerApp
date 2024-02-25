# Expense Tracker App

This is the documentation for my Expense Tracker App. The Database contains 3 collections: users, expenses and transactions. To obtain balances of each user the transactions database has been created which stores transaction between each user when an expense is created. The API endpoints and documentation is as described below.

## API Documentation

### OpenAPI Schema

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "FastAPI",
    "version": "0.1.0"
  },
  "paths": {
    "/users/": {
      "get": {
        "summary": "Get Users",
        "operationId": "get_users_users__get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "items": {
                    "$ref": "#/components/schemas/DbUser"
                  },
                  "type": "array",
                  "title": "Response Get Users Users  Get"
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "Add User",
        "operationId": "add_user_users__post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/UserResponse"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/users/{user_id}": {
      "get": {
        "summary": "Get User",
        "operationId": "get_user_users__user_id__get",
        "parameters": [
          {
            "name": "user_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "User Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/UserResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/users/balance/{user_id}": {
      "get": {
        "summary": "Get Balances",
        "operationId": "get_balances_users_balance__user_id__get",
        "parameters": [
          {
            "name": "user_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "User Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "$ref": "#/components/schemas/BalanceResponse"
                  },
                  "title": "Response Get Balances Users Balance  User Id  Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/expenses/{expense_id}": {
      "get": {
        "summary": "Get Expense",
        "operationId": "get_expense_expenses__expense_id__get",
        "parameters": [
          {
            "name": "expense_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Expense Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ExpenseResponse"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/expenses/": {
      "post": {
        "summary": "Add Expense",
        "operationId": "add_expense_expenses__post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/AddExpensePayload"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/expenses/upload_image/{expense_id}": {
      "patch": {
        "summary": "Upload Image",
        "operationId": "upload_image_expenses_upload_image__expense_id__patch",
        "parameters": [
          {
            "name": "expense_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Expense Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "multipart/form-data": {
              "schema": {
                "$ref": "#/components/schemas/Body_upload_image_expenses_upload_image__expense_id__patch"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/expenses/user/{user_id}": {
      "get": {
        "summary": "Get Expenses Of User",
        "operationId": "get_expenses_of_user_expenses_user__user_id__get",
        "parameters": [
          {
            "name": "user_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "User Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "$ref": "#/components/schemas/ExpenseResponse"
                  },
                  "title": "Response Get Expenses Of User Expenses User  User Id  Get"
                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "AddExpensePayload": {
        "properties": {
          "amount": {
            "type": "number",
            "maximum": 10000000,
            "minimum": 0,
            "title": "Amount",
            "description": "Amount should be between 0 and 1,00,00,000."
          },
          "payee_id": {
            "type": "string",
            "title": "Payee Id"
          },
          "expense_type": {
            "$ref": "#/components/schemas/ExpenseSplitType"
          },
          "name": {
            "anyOf": [
              {
                "type": "string",
                "maxLength": 128
              },
              {
                "type": "null"
              }
            ],
            "title": "Name"
          },
          "notes": {
            "anyOf": [
              {
                "type": "string",
                "maxLength": 500
              },
              {
                "type": "null"
              }
            ],
            "title": "Notes"
          },
          "participants": {
            "items": {
              "$ref": "#/components/schemas/Participant"
            },
            "type": "array",
            "title": "Participants"
          }
        },
        "type": "object",
        "required": [
          "amount",
          "payee_id",
          "expense_type",
          "participants"
        ],
        "title": "AddExpensePayload"
      },
      "BalanceResponse": {
        "properties": {
          "user": {
            "type": "string",
            "title": "User"
          },
          "amount_owed": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "integer"
              }
            ],
            "title": "Amount Owed"
          }
        },
        "type": "object",
        "required": [
          "user",
          "amount_owed"
        ],
        "title": "BalanceResponse"
      },
      "Body_upload_image_expenses_upload_image__expense_id__patch": {
        "properties": {
          "files": {
            "items": {
              "type": "string",
              "format": "binary"
            },
            "type": "array",
            "title": "Files"
          }
        },
        "type": "object",
        "required": [
          "files"
        ],
        "title": "Body_upload_image_expenses_upload_image__expense_id__patch"
      },
      "DbUser": {
        "properties": {
          "_id": {
            "type": "string",
            "title": " Id"
          },
          "name": {
            "type": "string",
            "maxLength": 128,
            "title": "Name"
          },
          "email": {
            "type": "string",
            "maxLength": 256,
            "format": "email",
            "title": "Email"
          },
          "phone": {
            "type": "integer",
            "title": "Phone"
          }
        },
        "type": "object",
        "required": [
          "name",
          "email",
          "phone"
        ],
        "title": "DbUser"
      },
      "ExpenseResponse": {
        "properties": {
          "amount": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "integer"
              }
            ],
            "title": "Amount"
          },
          "date": {
            "type": "string",
            "format": "date-time",
            "title": "Date"
          },
          "name": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Name"
          },
          "notes": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Notes"
          },
          "participants": {
            "items": {
              "$ref": "#/components/schemas/User"
            },
            "type": "array",
            "title": "Participants"
          }
        },
        "type": "object",
        "required": [
          "amount",
          "date",
          "name",
          "notes",
          "participants"
        ],
        "title": "ExpenseResponse"
      },
      "ExpenseSplitType": {
        "type": "string",
        "enum": [
          "EQUAL",
          "EXACT",
          "PERCENT",
          "WEIGHT"
        ],
        "title": "ExpenseSplitType"
      },
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            },
            "type": "array",
            "title": "Detail"
          }
        },
        "type": "object",
        "title": "HTTPValidationError"
      },
      "Participant": {
        "properties": {
          "user_id": {
            "type": "string",
            "title": "User Id"
          },
          "contribution": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "title": "Contribution"
          }
        },
        "type": "object",
        "required": [
          "user_id",
          "contribution"
        ],
        "title": "Participant"
      },
      "User": {
        "properties": {
          "user_id": {
            "type": "string",
            "title": "User Id"
          },
          "amount": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "integer"
              }
            ],
            "title": "Amount"
          }
        },
        "type": "object",
        "required": [
          "user_id",
          "amount"
        ],
        "title": "User"
      },
      "UserResponse": {
        "properties": {
          "name": {
            "type": "string",
            "maxLength": 128,
            "title": "Name"
          },
          "email": {
            "type": "string",
            "maxLength": 256,
            "format": "email",
            "title": "Email"
          },
          "phone": {
            "type": "integer",
            "title": "Phone"
          }
        },
        "type": "object",
        "required": [
          "name",
          "email",
          "phone"
        ],
        "title": "UserResponse"
      },
      "ValidationError": {
        "properties": {
          "loc": {
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "type": "array",
            "title": "Location"
          },
          "msg": {
            "type": "string",
            "title": "Message"
          },
          "type": {
            "type": "string",
            "title": "Error Type"
          }
        },
        "type": "object",
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "title": "ValidationError"
      }
    }
  }
}
```
