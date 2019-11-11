## Overview

The RTM protocol is our wire protocol, which enables direct two-way
communication between a client and RTM. Clients communicate with RTM by
establishing a secure WebSocket connection and exchanging JSON- or
CBOR-encoded units.

RTM implements the publish-subscribe pattern where users publish
messages to a channel and all subscribers to that channel receive those
messages.

The RTM API defines the structure, rules and semantics for exchanging
the JSON objects. We call these JSON objects Protocol Data Units
(PDUs). A PDU can carry a request to RTM to perform a particular action
(such as to publish a message), its response from RTM, or an
unsolicited message, such as subscription data.

### Message order guarantees

RTM  forwards published messages to the subscribers in the same order
as it received them. The order of messages between different publishers
is not guaranteed. All subscribers will receive the published messages
in the same order.

## Protocol Data Unit (PDU)

Definition

   A PDU is a unit, formatted in JSON or CBOR, with a specific structure
   enabling meaningful communication between RTM and clients. Each PDU is
   encoded into a single WebSocket frame. RTM supports UTF-8.

PDU encoding

   We use custom self-explanatory "mini schema" to define the format of
   JSON PDUs. It uses JSON syntax to describe fields, followed by
   their type or placeholder values (which in turned are defined the same
   way). Fields order does not matter. See [41]Mini-schema Reference for
   more details.

   The following mini schema  defines the structure of a PDU. Note that
   this structure holds for all PDUs in RTM API.

```
{
     "action": string,
     "id": string | integer OPTIONAL,
     "body": object
}
```

JSON PDUs

   JSON PDUs are JSON objects. In languages other than JavaScript, use a
   JSON API to convert native objects to a canonical JSON form.

WebSocket for RTM

Endpoint

   The WebSocket connection string for RTM has the syntax:
<endpoint>/<rtm_version>?appkey=<appkey>

     * <endpoint>: Endpoint string from Dev Portal, for example
       wss://example.com
     * <rtm_version>: Current version of RTM, for example v2. The current
       version is listed at the beginning of the RTM API documentation
     * <appkey>: Appkey from Dev Portal

   For example:
wss://example.com/v2?appkey=46832Af7f7cba8df8Fa2Bd5CE8B7D99E

Content negotiation

   Because RTM supports both JSON and CBOR, you need to specify the PDU
   format you want to use. To do this, specify the
   Sec-WebSocket-Protocol: subprotocol header field in your WebSocket
   handshake request. The permissible values are json and cbor. For
   backwards compatibility, RTM doesn't require the field, but if you omit
   it RTM assumes that it's set to json. For this reason, you must always
   specify Sec-WebSocket-Protocol: cbor to use CBOR PDUs.

   The PDU format of messages you receive from a channel is independent of
   the format that the publisher used. For example, if the publisher uses
   JSON to publish messages, but you connect to RTM and request CBOR, you
   receive CBOR messages.

PDU types

   A PDU can represent any of the following units of communication:
     * A request to RTM. A request to perform an action, for example, to
       publish a message.
     * A response from RTM. The response to a client request.
     * Unsolicited subscription messages from RTM. Messages as they have
       been published to the channel for simple subscriptions, or
       resulting messages for subscriptions with views.
     * An unsolicited error or information updates. Channel-specific
       informational or error messages, or system error messages, sent by
       RTM to the client.

PDU size

   User generated "payload" is limited to 64kB: such as message in the
   Publish PDU or filter in the Subscribe PDU. The total size of an
   unparsed PDU is limited to 65kB. RTM may drop the client connection if
   the size exceeds the limit.

PDU fields

action field

   The action field specifies the purpose of a PDU and determines the
   content of the body.

   The action field consists of up to three components separated by
   forward slash: <service>/<operation>/<outcome>.

   The following table explains the meaning of each component, as well as
   the rule for parsing it out from the full action string value:

Action component

Meaning

Parsing rules

   service

   Name of the service responsible for handling incoming requests or
   sending responses and unsolicited PDUs.

   The first part of the action string up to the first backslash character
   `/'.

   operation

   Operation the client wants the service to perform.

   After the first backslash character "/" up to the outcome or end of the
   string.

   Note that it may contain backslashes as part of the operation.

   outcome

   Represents the result of the request or the type of information
   provided to the client.

   Present only in responses and unsolicited PDUs. The part after the last
   backslash "/".

   The following table summarizes possible values used in the action
   field:

Service

Operation

Outcome

   rtm

   publish
   subscribe
   unsubscribe

   read
   write
   delete

   ok
   error

   subscription

   data
   info
   ok
   error

   auth

   handshake
   authenticate

   ok
   error

id field

   The id field in a request PDU instructs RTM to send a response and
   enables a client to match a response to a request. If the id field is
   not present in a request, RTM does not acknowledge it: no response will
   be sent to a client, regardless of the outcome. Note that id field and
   its semantics applies to every PDU in the RTM protocol.

   The id field can be an integer or a string.

   Even though specifying id field in a request is optional, only a few
   cases benefit from omitting it (e.g. high throughput publishing);  some
   operation cannot be completed without id at all (e.g. authentication).
   Clients should specify id in a request, unless client logic identified
   a concrete motivation not to do so, for a specific use case.

   Use the following rules and guidelines with the id field:

Rule/Guideline

Description

   Include id field to get a response from RTM

   In most cases, there is no significant traffic savings from omitting
   the id but by doing so, client forfeits an opportunity to detect
   failing requests (error outcome).

   Avoid reusing id value in different requests

   RTM does not enforce uniqueness on the id field. Two requests with the
   same id are treated as two separate requests by RTM.

body field

   The body field's content is specific to the PDU's action. The structure
   and semantics of the body field's content must be followed for each
   action field type.

   See the definitions of the specific PDU types.

Channels [42]Direct link

   Channels are named streams of messages.

   A channel is unique per Dev Portal project. If two projects have
   channels with the same name, RTM treats them as separate channels: they
   have their own content, history, settings, permissions, etc.

Subscription

   Subscriptions are clients' interest in messages published to a channel,
   accepted and served by RTM.

   In the simplest case, a subscription establishes a client's interest in
   all messages as they arrive in a channel. Clients may also request a
   subscription to include past messages (see history and position). In
   more involved cases, message data can be filtered or/and transformed
   (see [43]Views).

Position

   A position is a message offset relative to other messages in the
   channel. It uniquely identifies the location of the message in the
   channel and may refer to an expired (no longer stored), available
   (stored, retrievable), or future (not yet occupied location) message.

   The next channel position is the first available unoccupied position in
   a channel. The next published message to arrive is placed at this
   position.

   The position field can be used to read a particular message from a
   channel or to subscribe from a specific position, typically in order to
   avoid skipping messages when re-subscribing.

Operation

PDU type

Position meaning

   RTM includes position (in responses or data PDUs).
   publish, write, delete ok response Location of the published message
   subscribe ok response Location of the first message to be received for
   the subscription
   unsubscribe ok response Location that can be used to seamlessly
   resubscribe
   subscription unsolicited data next location after the last message
   contained in the PDU. Client can use this location to resubscribe
   preserving stream continuity (no message loss).
   User can include position (in request PDUs)
   subscribe request Location to start a subscription at
   read request Location from which to read a message

Implicit channel creation and deletion

   Channel instances are automatically created by RTM on demand: upon the
   first subscribe or publish request to a specified channel name, RTM
   creates a corresponding channel instance.

   RTM automatically garbage collects channels when it is safe to do so
   (channel is empty and no one has been accessing it for some time).

   Channel instance creation and deletion should not be confused with
   managing channel bookkeeping in Dev Portal, such as setting permissions
   or history for specific channel names or namespaces.

Channel permissions

   Channel access can be controlled by configuring publish and subscribe
   permissions (akin to write/read permissions) in Dev Portal.

Channel history

   In addition to forwarding published messages to all subscribers, RTM
   also stores all messages for at least 1 minute. Additionally, longer
   storage is available with channel history: users can configure how many
   messages should be stored for a longer period of time for a given
   channel. History settings are configured in Dev Portal and default to
   one message for 6 hours.

   A subscription to a channel can be requested starting at a historical
   message; similarly read operation can retrieve messages published in
   the past.

Channel names

   Channel names are case sensitive.

   Channel names starting with character `$' are reserved by RTM.

## Publish PDU

   Messages can be published to a channel by sending a Publish PDU request
   to RTM.

   The following specification shows the publish request and response
   PDUs:

Request

```
{
  "action":"rtm/publish",
  "id":RequestId OPTIONAL,
  "body":{
    "channel":ChannelName,
    "message":Message
  }
}
```

Response (OK)

```
{
  "action":"rtm/publish/ok",
  "id": RequestId,
  "body":{
    "position":Position
  }
}
```

Response (error)

```
{
  "action":"rtm/publish/error",
  "id":RequestId,
  "body":{
    "error":ErrorName,
    "reason":ErrorReason
   }
}
```

Field

Type

Description

   ChannelName

   string

   The name of the channel to publish to.

   Message

   value

   The message to publish to the channel.

   Message size is limited to 64 kB. RTM may disconnect if the size
   exceeds the limit. See PDU Size in [45]Protocol Data Unit
   (PDU) section.
   Although any value is allowed, publishers should
   publish object messages so that subscribers using streamviews see the
   message. See [46]Views.

   Position

   string

   The channel location of the published message. See Position in
   [47]Channels.

   ErrorName

   string
   Possible errors are listed in the sections following this table.

   ErrorReason

   text
   Human readable error description. See [48]Error Reference.

Unclassified errors

   RTM may return the following unclassified errors:
     * "authorization_denied"
     * "cbor_parse_error"
     * "invalid_format"
     * "invalid_operation"
     * "invalid_service"
     * "json_parse_error"

   To learn more about any of these errors, see [49]Unclassified Errors.

Publish-specific errors

   The following errors are specific to a publish operation:

error value

Meaning

   "channel_quota_exceeded" Your publish request specified a channel that
   doesn't yet exist. RTM couldn't create the channel, because you
   exceeded your quota for the number of channels per project.

   The "action" field is always "rtm/publish/error"

## Subscribe PDU

   A client subscribes to a channel by sending a request Subscribe PDU to
   RTM.

Position

   By default, a new subscription starts at the next channel position
   (from the next published message, see position in [51]Channels). That
   is, no previously published (historic) messages are returned. A client
   may start a subscription at an  earlier (historic) message by
   specifying the position in the subscribe request PDU.

subscription_id

   A subscription is identified by the subscription_id field. Multiple
   subscriptions can be made to the same channel, as long as different
   subscription id's are used.

   For a subscription without a view (default), the subscription_id must
   be equal to the channel name, and is optional.

   For a subscription with a view, the subscription_id field is required
   and the channel field is optional (the channel name must match what is
   specified in the filter (view) field).

Subscribe without streamview (no filter field)

Request

```
{
  "action":"rtm/subscribe",
  "id":RequestId OPTIONAL,
  "body":{
    "channel":ChannelName,
    "subscription_id":SubId OPTIONAL,
    "force":Force OPTIONAL,
    "fast_forward":FastForward OPTIONAL,
    "position":Position OPTIONAL,
    "history":{
      "count":Count OPTIONAL,
      "age":Age OPTIONAL
    } OPTIONAL
  }
}
```

Response (ok)

```
{
  "action":"rtm/subscribe/ok",
  "id":RequestId
  "body":{
    "position":Position,
    "subscription_id":SubId
  }
}
```

Response (error)

```
{
  "action":"rtm/subscribe/error",
  "id":RequestId,
  "body":{
    "error":ErrorName,
    "reason":ErrorReason OPTIONAL,
    "subscription_id":SubId
   }
}
```

Subscribe with streamview (filter field)

Request

```
{
  "action":"rtm/subscribe",
  "id":RequestId OPTIONAL,
  "body":{
    "filter":SQL,
    "subscription_id":SubId,
    "force":Force OPTIONAL,
    "fast_forward":FastForward OPTIONAL,
    "period":Period OPTIONAL,
    "position":Position OPTIONAL,
    "history":{
      "count":Count OPTIONAL,
      "age":Age OPTIONAL
    } OPTIONAL
  }
}
```

Response (ok)

```
{
  "action":"rtm/subscribe/ok",
  "id":RequestId,
  "body":{
    "position":Position,
    "subscription_id":SubId
  }
}
```

Response (error)

```
{
  "action":"rtm/subscribe/error",
  "id":RequestId,
  "body":{
    "error":ErrorName,
    "reason":ErrorReason OPTIONAL,
    "subscription_id":SubId
   }
}
```

Field

Type

Description

   ChannelName

   string

   The name of the channel to subscribe to.

   SubId

   string

   Either a channel name or a unique client-generated identifier for the
   subscription (when applicable)

   Position

   string

   Channel location to start the subscription at. Default is the next
   channel position.

   See position in [52]Channels section.

   SQL

   string

   SQL statement to run on messages before sending them to the client. The
   size is limited to 64 kB. See [53]Views.

   Period

   int

   Time partition on the channel messages, in seconds, for which RTM
   aggregates the view result per partition. See [54]Views.

   The default value is 1 second. The maximum value is 60 seconds.

   Force

   boolean

   Directs RTM how to act if your client already has an existing
   subscription with the same value of subscription_id.

   If you provide a new value for subscription_id, RTM removes the
   existing subscription and creates a new subscription with the fields
   you specify in body.

   If you provide a new value for channel, RTM removes the existing
   subscription and creates a new subscription with the fields you specify
   in body. If you specify a value for filter, the value of channel must
   be the same as the channel name you specify in the streamSQL for the
   filter field.

   If you specify the filter property or period property or both, RTM
   updates the values and ignores any other fields in body.

   FastForward

   boolean

   Specifies preferred behavior if an out_of_sync error situation occurs.

   true directs RTM to fast-forward the subscription to the oldest
   available message

   false directs RTM to force unsubscription

   Default is false

   history

   object

   Contains a non-negative integer in the age field or count field.

   See history in [55]Channels section.

   history:{} returns no history.

   Age

   int

   RTM starts the subscription this many seconds earlier than the value in
   the position field.

   Count

   int

   RTM starts the subscription this many messages before the value in the
   position field.

   ErrorName

   string

   Possible errors are listed in the sections following this table.

   ErrorReason

   text

   Human readable error description. See [56]Error Reference.

   RequestId

   int | string

   See id field in [57]PDU section.

Unclassified errors

   RTM may return the following unclassified errors:
     * "authorization_denied"
     * "cbor_parse_error"
     * "invalid_format"
     * "invalid_operation"
     * "invalid_service"
     * "json_parse_error"

   To learn more about any of these errors, see [58]Unclassified Errors.

Subscribe-specific errors

error value

Meaning

   "already_subscribed" You requested a new subscription with
   subscription_id set to an active subscription id, and you didn't
   specify "force" : true.
   "expired_position" RTM expired the message at the position you
   specified in position. The message is no longer available.
   "invalid_filter" (for a streamview subscription only): The stream SQL
   you specified in filter is invalid.
   "subscription_quota_exceeded" You tried to add a subscription or
   streamview, but you exceeded the quota for the number of subscriptions
   or streamviews per project.

   The "action" field is always "action":"rtm/subscribe/error".

out_of_sync and fast_forward

   RTM sends subscription messages to the client as fast as the physical
   network link to the client allows it. If the rate of incoming
   (published) messages is higher than the outgoing rate (rate at which
   messages are delivered to a particular client subscription), we say
   that a client subscription is falling behind. If this situation
   persists, undelivered messages accumulate on the RTM side and
   eventually RTM expires (deletes) them. By default, messages are deleted
   after 60 seconds and the last message in a channel - after 6h. We call
   this situation out_of_sync: messages stream continuity cannot be
   sustained for a subscriber; message drop is inevitable.

   Subscriber can change this behavior by setting the fast_forward field
   to true in the request Subscribe PDU. In this case, RTM "fast-forwards"
   the client to the oldest not yet deleted message, instead of forcing
   unsubscription, and sends an info Subscription PDU.

Updating a subscription

   filter and period fields can be changed on-the-fly for a pre-existing
   active subscription: by sending a Subscribe PDU with the force field
   set to true. Without "force":true, RTM responds with an
   already_subscribed error and does not update the current subscription.

## Subscription PDUs (unsolicited)

   RTM sends subscription data (channel messages) or subscription related
   status (info or error) using subscription PDUs.

   Subscription PDU can be:
     * data.  A subscription data PDU delivers channel messages (possibly
       filtered and transformed messages in case of a viewed
       subscription). Note that a single subscription data PDU can contain
       multiple messages grouped in the array messages field (for
       optimization purposes).
     * info. A subscription Info PDU contains information about a
       subscription, which includes the type of info and the reason why
       RTM sent it. For a fast_forward info, it also includes the count of
       skipped messages due to RTM fast-forwarding the subscription.
     * error. A subscription error PDU notifies of subscription
       termination (forceful unsubscription) due to a subscription-related
       error. For example, if a client subscription falls behind and
       fast-forward has not been enabled, RTM sends an out_of_sync error
       and unsubscribes the client (see out_of_sync in [60]Subscribe PDU
       section).

Subscription data

```
{
  "action":"rtm/subscription/data",
  "body":{
    "position":Position,
    "messages":[Message]*,
    "subscription_id":SubId
   }
}
```

Subscription info

```
{
  "action":"rtm/subscription/info",
  "body":{
    "info":InfoType,
    "reason":InfoReason,
    "position":Position,
    "subscription_id:SubId,
    "missed_message_count":Count OPTIONAL
   }
}
```

Subscription error

```
{
 "action":"rtm/subscription/error",
  "body":{
    "error":ErrorName,
    "reason":ErrorReason,
    "position":Position,
    "subscription_id":SubId,
    "missed_message_count":Count OPTIONAL
   }
}
```

Field

Type

Description

   Position

   string

   See position in the [61]Channels section.
   Provided to enable clients to resubscribe preserving stream continuity
   (in the event of a disconnect).

   Message

   value

   A channel message (as it was published, or - when applicable - a
   message result according to the subscription view)

   SubId

   string

   Id for the subscription for which the PDU was sent.

   InfoType

   string

   Information type. See Service-Specific Info Messages.

   InfoReason

   text

   In the sections following this table, see "Unsolicited subscribe info
   messages".

   Count

   int

   Number of skipped messages in the channel.

   ErrorName

   string

   Possible errors are listed in the sections following this table.

   ErrorReason

   text

   Human readable error description. See [62]Error Reference.

Unsolicited subscribe errors

   RTM may return one of these errors for an active subscription:

error value

Meaning

   "out_of_sync" The message position for the subscription is pointing to
   an expired message, and your subscribe PDU didn't specify
   "fast_forward" : true. RTM unsubscribes you, and it may drop your
   connection.
   expired_position Your subscribe PDU specified the "position" field, but
   its value points to an expired message.

   The "action" field is always "action":"rtm/subscription/error".

Unsolicited subscribe info messages

   RTM may return this info message for an active subscription:

info value

Meaning

   fast_forward Because your subscribe PDU specified "fast_forward" :
   true, RTM performed a fast forward in response to an out of sync
   condition. You receive this info PDU in addition to an error PDU with
   error set to "expired_position".

   The "action" field is always "action":"rtm/subscription/info".

## Unsubscribe PDU

   A subscriber requests to terminate its subscription by sending an
   Unsubscribe PDU request to RTM.

   In case a client endpoint has multiple subscriptions to the same
   channel, it must send a PDU for each subscription it wants to end.

Request

```
{
  "action":"rtm/unsubscribe",
  "id":RequestId OPTIONAL,
  "body":{
    "subscription_id":SubId
  }
}
```

Response (ok)

```
{
  "action":"rtm/unsubscribe/ok",
  "id":RequestId,
  "body":{
    "position":Position,
    "subscription_id":SubId
  }
}
```

Response (error)

```
{
  "action":"rtm/unsubscribe/error",
  "id":RequestId,
  "body":{
    "error":ErrorName,
    "reason":ErrorReason,
    "subscription_id":SubId OPTIONAL
   }
}
```

Field

Type

Description

   SubId

   string

   Id of the subscription that you want to cancel.

   Position

   string

   RTM response includes current location in the channel message stream at
   the time unsubscribe operation has completed.
   Enables a client to resubscribe to the channel from the position where
   it unsubscribed

   ErrorName

   string

   Possible errors are listed in the sections following this table.

   ErrorReason

   text

   Human readable error description. See [64]Error Reference.

Unclassified errors

   RTM may return the following unclassified errors:
     * "authorization_denied"
     * "cbor_parse_error"
     * "invalid_format"
     * "invalid_operation"
     * "invalid_service"
     * "json_parse_error"

   To learn more about any of these errors, see [65]Unclassified Errors.

Unsubscribe-specific errors

   The following errors are specific to an unsubscribe operation:

error value

Meaning

   "not_subscribed" You tried to unsubscribe from a subscription that
   doesn't exist.

   The "action" field is always "action":"rtm/unsubscribe/error".

## Read PDU

   A particular message in a channel can be retrieved by sending a Read
   PDU request to RTM.

   RTM returns the message at the position specified in the request. If
   there is no position specified, RTM defaults to the position of the
   latest message in the channel. A null message in the response PDU means
   that there were no messages at that position.

Request

```
{
  "action":"rtm/read",
  "id":RequestId OPTIONAL,
  "body":{
    "channel":ChannelName,
    "position":Position OPTIONAL
   }
}
```

Response (ok)

```
{
  "action":"rtm/read/ok",
  "id":RequestId,
  "body":{
    "position":Position,
    "message":Message
  }
}
```

Response (error)

```
{
  "action":"rtm/read/error",
  "id":RequestId,
  "body":{
    "error":ErrorName,
    "reason":ErrorReason
  }
}
```

Field

Type

Description

   ChannelName

   string

   The name of the channel to read from.

   Position

   string

   The channel location to retrieve a message at.

   See position in the Channels section.

   Message

   value

   Message returned by RTM.

   ErrorName

   string

   Possible errors are listed in the sections following this table.

   ErrorReason

   text

   Human readable error description. See [67]Error Reference.

   RequestId

   int | string

   See id Field in the [68]Channels section.

Unclassified errors

   RTM may return the following unclassified errors:
     * "authorization_denied"
     * "cbor_parse_error"
     * "invalid_format"
     * "invalid_operation"
     * "invalid_service"
     * "json_parse_error"

   To learn more about any of these errors, see [69]Unclassified Errors.

Read-specific errors

   The following errors are specific to a read operation:

error value

Meaning

   "expired_position" The message at the position you tried to read from
   no longer exists, because RTM expired it.

   The "action" field is always "action":"rtm/read/error".

## Write PDU

   Write PDU is provided for key-value (dictionary storage) semantics:
   channel name represents a key and the last (and the only used) message
   the channel represents a value. In other words, a channel serves as a
   dictionary entry.

   Current implementation and specifications are the same as publish PDU
   but using write operation in action: "action":"rtm/write".

## Delete PDU

   The delete PDU is provided for key-value (dictionary storage) semantics
   to erase a value for a given key. The key is represented by a channel,
   and only the last message in the channel is relevant (represents the
   value). Hence, publishing a null value serves as deletion of the the
   previous value (if any).

   Sending a delete PDU request is the same as publishing or writing a
   null value to the channel.

   A delete operation requires publish permission.

Request

```
{
  "action":"rtm/delete",
  "id":RequestId OPTIONAL,
  "body":{
    "channel":Channel
  }
}
```

Response (ok)

```
{
  "action":"rtm/delete/ok",
  "id":RequestId,
  "body":{
    "position":Position OPTIONAL
  }
}
```

Response (error)

```
{
  "action":"rtm/delete/error",
  "id":RequestId,
  "body":{
    "error":ErrorName,
    "reason":ErrorReason
  }
}
```

Field

Type

Description

   ChannelName

   string

   The name of the channel.

   Position

   string

   Present only in a response.

   Channel location at which the message has been deleted, when purge is
   false.

   When purge is true, position is not returned.

   See position in the [72]Channels section.

   ErrorName

   string

   Possible errors are listed in the sections following this table.

   ErrorReason

   text

   Human readable error description. See [73]Error Reference.

   RequestId

   int | string

   See id field in the [74]PDU section.

Unclassified errors

   RTM may return the following unclassified errors:
     * "authorization_denied"
     * "cbor_parse_error"
     * "invalid_format"
     * "invalid_operation"
     * "invalid_service"
     * "json_parse_error"

   To learn more about any of these errors, see [75]Unclassified Errors.

Delete-specific errors

   The following errors are specific to a delete operation:

error value

Meaning

   "expired_position" The message you tried to delete no longer exists,
   because RTM expired it.

   The "action" field is always "action":"rtm/delete/error".

Using delete

   Deleting a channel message is the same as publishing or writing null to
   the channel. For example, these three requests to RTM accomplish
   identical result:

   {"action":"rtm/publish","body":{"channel":"x","message":null}}

   {"action":"rtm/write","body":{"channel":"x","message":null}}

   {"action":"rtm/delete","body":{"channel":"x"}}

## Handshake & Authenticate PDUs

   RTM uses role-based authentication and authorization. Roles and their
   channel permissions are configured in [77]Dev Portal.

   When you first connect to RTM, your client is established with
   the default role. You can acquire different permissions by
   authenticating for a different role. You do this in a two-step process
   using the handshake and then the authenticate PDU.

Handshake PDU

   To start the authentication process, you send a handshake PDU to obtain
   a nonce that you use to construct an authentication hash.

   If the request succeeds, RTM returns the nonce. In case of an error,
   RTM cancels the handshake request. For example, an error may occur if
   the role you specify doesn't exist in the Dev Portal.

Request

```
{
  "action":"auth/handshake",
  "id":RequestId OPTIONAL
  "body":{
    "method":AuthMethod,
    "data":{
      "role":Role
     }
  }
}
```

Response (ok)

```
{
  "action":"auth/handshake/ok",
  "id":RequestId,
  "body":{
    "data":{
      "nonce":Nonce
     }
  }
}
```

Response (error)

```
{
  "action":"auth/handshake/error",
  "id":RequestId,
  "body":{
    "error":ErrorName,
    "reason":ErrorReason
   }
  }
}
```

Field

Type

Description

   AuthMethod

   string

   Method of authentication to perform. Only "role_secret" is currently
   supported.

   Role

   string

   Role to authenticate as.

   Nonce

   string

   Cryptographic random value to be combined with the secret by the client
   to produce the hash. Hash is sent in rtm/authenticate request.

   ErrorName

   string

   Possible errors are listed in the sections following this table.

   ErrorReason

   text

   Human readable error description. See [78]Error Reference.

Unclassified errors

   RTM may return the following unclassified errors:
     * "authorization_denied"
     * "cbor_parse_error"
     * "invalid_format"
     * "invalid_operation"
     * "invalid_service"
     * "json_parse_error"

   To learn more about any of these errors, see [79]Unclassified Errors.

Handshake-specific errors

   RTM may return the following errors in response to a handshake request:

error value

Meaning

   "auth_method_not_allowed" In the handshake PDU, method is not set to
   "role_secret".

   The "action" field is always "action":"auth/handshake/error".

Authenticate PDU

   You send the authenticate PDU to complete the authentication process.
   After authentication is complete, your client has the permissions
   associated with the role with which it has authenticated.

   In case of an error, RTM cancels the entire authentication request.
   This can occur, for example, if your calculated hash doesn't match the
   value calculated by RTM, or if the role you specify doesn't exist in
   the Dev Portal.

Request

```
{
  "action":"auth/authenticate",
  "id":RequestId OPTIONAL,
  "body":{
    "method":AuthMethod,
    "credentials":{
      "hash":Hash
    }
  }
}
```

Response (ok)

```
{
  "action":"auth/authenticate/ok",
  "id":RequestId,
  "body":{}
}
```

Response (error)

```
{
  "action":"auth/authenticate/error",
  "id":RequestId,
  "body":{
    "error":ErrorName
    "reason":ErrorReason
  }
}
```

Field

Type

Description

   AuthMethod

   text

   Method of authentication to perform. Only "role_secret" is currently
   supported.

   Role

   text

   Role to authenticate as.

   Project roles and their permissions  are managed in Dev Portal.

   Hash

   string

   HMAC-MD5 hash value computed for the secret key and the nonce received
   in rtm/handshake/ok.

   ErrorName

   string

   Possible errors are listed in the sections following this table.

   ErrorReason

   text

   Human readable error description. See [80]Error Reference.

Unclassified errors

   RTM may return the following unclassified errors:
     * "authorization_denied"
     * "cbor_parse_error"
     * "invalid_format"
     * "invalid_operation"
     * "invalid_service"
     * "json_parse_error"

   To learn more about any of these errors, see [81]Unclassified Errors.

Authenticate-specific errors

   RTM may return the following errors in response to a authentication
   request:

error value

Meaning

   "authentication_failed" In your authentication PDU, the value of "hash"
   is invalid.
   "auth_method_not_allowed" In the authentication PDU, the value of
   "method" is not set to "role_secret".

   The "action" field is always "action":"auth/authenticate/error".

Hash computation

   The hash is calculated for a secret key (K) and a nonce (N).  The
   secret key is obtained from the Dev Portal; the nonce is received in
   handshake response PDU.

   Hash = base64( HMAC-MD5( utf8(K), utf8(N) ) )

   Existing HMAC-MD5 implementations are commonly available for any
   language. For completeness:

   HMAC-MD5 is the algorithm specified in [[82]RFC 2104] using MD5
   [[83]RFC 1321] as the underlying hash function. base64 is a string
   representation of a byte array described in [[84]RFC 3548]. Note that
   the result of the base64 operation is the actual hash value and shall
   be used as it is. utf8 is the binary representation of string described
   in [[85]RFC 3629].

   Hash computation example
```
Let secret key K = "secret-key" and nonce N = "nonce"

utf8(K) = [73 65 63 72 65 74 2D 6B 65 79]
utf8(N) = [6E 6F 6E 63 65]
HMAC-MD5(utf8(SK), utf8(N)) = [1B 5D 80 F0 3B 74 45 D8 C7 37 1F 0F D2 57 22 F7]
hash = 'G12A8Dt0RdjHNx8P0lci9w=='
```

## Error Reference

   Every error includes error and reason fields. Additional fields may be
   present, specific to a PDU type.

Error PDU body

{
  "error": string,
  "reason": text,
  // other PDU-specific fields
}

error

   Name of the error. This string is intended for use in code.

reason

   Describes the error. This text is intended for human use; the text may
   change in the future and should not be used in code conditioning logic.

Error types

   Errors are categorized into two types:

Error Type

Description

   Unclassified

   Errors not associated with a particular operation. It may be unknown
   which operation is triggering it, or potentially affecting overall
   communication consistency.

   For example, if RTM cannot parse a PDU or cannot parse an action, it
   has no choice but to return a general system error.

   Operation-specific

   Errors returned in direct response to a request sent by a client, or
   unsolicited errors associated with a particular operation.

## Mini-schema Reference

   The format for a PDU is the concrete transfer syntax, and the PDU
   specifications used in this reference use a specific pattern based on
   JSON. The specifications may include different keywords as placeholders
   for the types of variable data.

Datatype

Examples

Description

   string

   "abc", "json-data", ""

   Any string that conforms to the JSON or CBOR string data structure,
   depending on the protocol in use.

   text

   "Hello, world"

   Similar to string, but contains text designed for users to read.

   int

   42, 3

   Any non-negative  signed integer value that conforms to the JSON number
   data structure, without fractions or exponents.

   CBOR has separate types for unsigned integer, negative integer, and
   float.

   boolean
   true, false

   For JSON, a boolean value.

   CBOR uses major type 7 additional type 20 for boolean false, and major
   type 7 additional type 21 for boolean true.

   value

   null, true, false, 42, "Hello, world", [3.14, 2.71], {"key":"value"}

   Any value of any valid JSON or CBOR type

   object

   {"key":"value"}

   Any JSON object or CBOR map

Structure

xxx =
type or placeholder

Examples

Description

   []* []
   [1, 2, 3]
   [int]*
   An array of zero or more xxx structures
   [xxx]+ [1]
   ["abc", "def"] An array of one or more values of the specified type or
   placeholders. For example, [string()]+ indicates non-empty array of
   strings.
   xxx1 | xxx2 true | false Value can be either of the two listed values
   or placeholders.
